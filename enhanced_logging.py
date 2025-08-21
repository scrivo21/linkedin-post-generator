"""
Enhanced Logging System for Discord LinkedIn Bot
Provides beautiful, color-coded terminal output with emojis and visual hierarchy
"""
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import os

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)  # Automatically reset colors after each print
    COLORAMA_AVAILABLE = True
except ImportError:
    # Fallback if colorama is not available
    COLORAMA_AVAILABLE = False
    class _FallbackColor:
        def __getattr__(self, name):
            return ""
    Fore = Back = Style = _FallbackColor()

class EnhancedFormatter(logging.Formatter):
    """
    Custom formatter with colors, emojis, and visual enhancements
    """
    
    # Color schemes for different log levels
    LEVEL_COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA
    }
    
    # Emojis for different log levels
    LEVEL_EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️ ',
        'ERROR': '❌',
        'CRITICAL': '💥'
    }
    
    # Component-specific emojis and colors
    COMPONENT_STYLES = {
        'discord_linkedin_bot': {'emoji': '🤖', 'color': Fore.BLUE},
        'linkedin_publisher': {'emoji': '🔗', 'color': Fore.BLUE},
        'db_monitor': {'emoji': '📊', 'color': Fore.CYAN},
        '__main__': {'emoji': '🚀', 'color': Fore.MAGENTA},
        'default': {'emoji': '📝', 'color': Fore.WHITE}
    }
    
    def __init__(self):
        super().__init__()
        # Check if terminal supports colors
        self.use_colors = self._supports_colors()
        
    def _supports_colors(self) -> bool:
        """Check if terminal supports colors"""
        if not COLORAMA_AVAILABLE:
            return False
            
        # Check environment variables
        if os.getenv('NO_COLOR') or os.getenv('TERM') == 'dumb':
            return False
            
        # Check if we're in CI/CD environment
        ci_environments = ['CI', 'CONTINUOUS_INTEGRATION', 'BUILD_NUMBER', 'GITHUB_ACTIONS']
        if any(os.getenv(var) for var in ci_environments):
            return False
            
        return sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and emojis"""
        if not self.use_colors:
            return self._format_plain(record)
        
        return self._format_enhanced(record)
    
    def _format_plain(self, record: logging.LogRecord) -> str:
        """Plain text formatting without colors"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        level_name = record.levelname.ljust(8)
        component = record.name.split('.')[-1]
        
        return f"[{timestamp}] {level_name} {component}: {record.getMessage()}"
    
    def _format_enhanced(self, record: logging.LogRecord) -> str:
        """Enhanced formatting with colors and emojis"""
        # Get color and emoji for log level
        level_color = self.LEVEL_COLORS.get(record.levelname, Fore.WHITE)
        level_emoji = self.LEVEL_EMOJIS.get(record.levelname, '📝')
        
        # Get component styling
        component_name = record.name.split('.')[-1]
        component_style = self.COMPONENT_STYLES.get(component_name, self.COMPONENT_STYLES['default'])
        component_emoji = component_style['emoji']
        component_color = component_style['color']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        timestamp_styled = f"{Style.DIM}{Fore.WHITE}[{timestamp}]{Style.RESET_ALL}"
        
        # Format level with emoji and color
        level_styled = f"{level_color}{level_emoji} {record.levelname.ljust(7)}{Style.RESET_ALL}"
        
        # Format component with emoji and color
        component_styled = f"{component_color}{component_emoji} {component_name}{Style.RESET_ALL}"
        
        # Format message based on content
        message = self._enhance_message(record.getMessage(), record.levelname)
        
        # Assemble final format
        formatted = f"{timestamp_styled} {level_styled} {component_styled}: {message}"
        
        # Add visual separators for errors and critical messages
        if record.levelname in ['ERROR', 'CRITICAL']:
            separator = f"{Fore.RED}{'─' * 80}{Style.RESET_ALL}"
            formatted = f"\n{separator}\n{formatted}\n{separator}"
        
        return formatted
    
    def _enhance_message(self, message: str, level: str) -> str:
        """Enhance message content with contextual styling"""
        if not self.use_colors:
            return message
        
        # Highlight specific patterns in messages
        enhanced = message
        
        # Highlight Discord-related content
        if 'discord' in message.lower():
            enhanced = enhanced.replace('Discord', f"{Fore.BLUE}Discord{Style.RESET_ALL}")
            
        # Highlight LinkedIn-related content  
        if 'linkedin' in message.lower():
            enhanced = enhanced.replace('LinkedIn', f"{Fore.BLUE}LinkedIn{Style.RESET_ALL}")
            enhanced = enhanced.replace('API', f"{Style.BRIGHT}API{Style.RESET_ALL}")
            
        # Highlight status messages
        if 'connected' in message.lower():
            enhanced = enhanced.replace('connected', f"{Fore.GREEN}connected{Style.RESET_ALL}")
        if 'failed' in message.lower():
            enhanced = enhanced.replace('failed', f"{Fore.RED}failed{Style.RESET_ALL}")
        if 'successful' in message.lower():
            enhanced = enhanced.replace('successful', f"{Fore.GREEN}successful{Style.RESET_ALL}")
            
        # Highlight numbers and IDs
        import re
        enhanced = re.sub(r'(\d+)', f"{Style.BRIGHT}\\1{Style.RESET_ALL}", enhanced)
        
        # Highlight post IDs
        enhanced = re.sub(r'(post_\w+|draft_\w+)', f"{Fore.CYAN}\\1{Style.RESET_ALL}", enhanced)
        
        return enhanced

class EnhancedLogger:
    """
    Enhanced logger with convenience methods for different message types
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_handler()
    
    def _setup_handler(self):
        """Setup enhanced handler if not already configured"""
        # Check if enhanced handler already exists
        enhanced_handler_exists = any(
            isinstance(h, logging.StreamHandler) and isinstance(h.formatter, EnhancedFormatter)
            for h in self.logger.handlers
        )
        
        if not enhanced_handler_exists:
            # Remove existing basic handlers
            for handler in self.logger.handlers.copy():
                if isinstance(handler, logging.StreamHandler):
                    self.logger.removeHandler(handler)
            
            # Add enhanced handler
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(EnhancedFormatter())
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            self.logger.propagate = False  # Prevent duplicate logging
    
    def startup_banner(self, title: str, version: str = None):
        """Display an impressive startup banner with ASCII art"""
        self._clear_terminal()
        
        if not EnhancedFormatter().use_colors:
            self.logger.info(f"Starting {title}")
            return
        
        # Create the main ASCII art banner
        ascii_art = self._get_discord_linkedin_ascii_art()
        
        # Create decorative border
        border_top = f"{Fore.CYAN}{'═' * 88}{Style.RESET_ALL}"
        border_bottom = f"{Fore.CYAN}{'═' * 88}{Style.RESET_ALL}"
        
        # Create info section
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        info_lines = [
            f"{Fore.YELLOW}┌{'─' * 86}┐{Style.RESET_ALL}",
            f"{Fore.YELLOW}│{Style.RESET_ALL} {Fore.GREEN}🚀 Status:{Style.RESET_ALL} {'Starting Discord LinkedIn Bot...':.<65} {Fore.GREEN}READY{Style.RESET_ALL} {Fore.YELLOW}│{Style.RESET_ALL}",
        ]
        
        if version:
            info_lines.append(f"{Fore.YELLOW}│{Style.RESET_ALL} {Fore.BLUE}📦 Version:{Style.RESET_ALL} {version:<73} {Fore.YELLOW}│{Style.RESET_ALL}")
        
        info_lines.extend([
            f"{Fore.YELLOW}│{Style.RESET_ALL} {Fore.MAGENTA}⏰ Started:{Style.RESET_ALL} {current_time:<72} {Fore.YELLOW}│{Style.RESET_ALL}",
            f"{Fore.YELLOW}│{Style.RESET_ALL} {Fore.CYAN}🤖 System:{Style.RESET_ALL} {'Enhanced Logging Enabled':<73} {Fore.YELLOW}│{Style.RESET_ALL}",
            f"{Fore.YELLOW}└{'─' * 86}┘{Style.RESET_ALL}"
        ])
        
        # Assemble the complete banner
        print("\n" * 2)  # Add some space at the top
        print(border_top)
        print(ascii_art)
        print(border_bottom)
        print()
        for line in info_lines:
            print(line)
        print()
        
        # Add a fun loading animation effect
        self._show_loading_animation()
        print()
    
    def _clear_terminal(self):
        """Clear the terminal screen"""
        import os
        import sys
        
        # Clear screen command for different operating systems
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # macOS and Linux
            os.system('clear')
    
    def _get_discord_linkedin_ascii_art(self):
        """Generate EPIC ASCII art for Discord LinkedIn Bot"""
        import random
        
        # Epic sparkle effects with more variety
        sparkles = ['✨', '⭐', '🌟', '💫', '⚡', '🔥', '💎', '🎯', '🚀', '💥', '🎆', '⚡']
        effects = [random.choice(sparkles) for _ in range(8)]
        
        # Perfectly aligned ASCII art
        art_lines = [
            f"",
            f"{effects[0]} {Fore.BLUE + Style.BRIGHT}    ██████╗ ██╗███████╗ ██████╗ ██████╗ ██████╗ ██████╗     {Style.RESET_ALL} {effects[1]}",
            f"    {Fore.BLUE + Style.BRIGHT}██╔══██╗██║██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗{Style.RESET_ALL}",
            f"    {Fore.BLUE + Style.BRIGHT}██║  ██║██║███████╗██║     ██║   ██║██████╔╝██║  ██║{Style.RESET_ALL}",
            f"    {Fore.BLUE + Style.BRIGHT}██║  ██║██║╚════██║██║     ██║   ██║██╔══██╗██║  ██║{Style.RESET_ALL}",
            f"    {Fore.BLUE + Style.BRIGHT}██████╔╝██║███████║╚██████╗╚██████╔╝██║  ██║██████╔╝{Style.RESET_ALL}",
            f"    {Fore.BLUE + Style.BRIGHT}╚═════╝ ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝{Style.RESET_ALL}",
            f"",
            f"{effects[2]} {Fore.CYAN + Style.BRIGHT}    ██╗     ██╗███╗   ██╗██╗  ██╗███████╗██████╗ ██╗███╗   ██╗    {Style.RESET_ALL} {effects[3]}",
            f"    {Fore.CYAN + Style.BRIGHT}██║     ██║████╗  ██║██║ ██╔╝██╔════╝██╔══██╗██║████╗  ██║{Style.RESET_ALL}",
            f"    {Fore.CYAN + Style.BRIGHT}██║     ██║██╔██╗ ██║█████╔╝ █████╗  ██║  ██║██║██╔██╗ ██║{Style.RESET_ALL}",
            f"    {Fore.CYAN + Style.BRIGHT}██║     ██║██║╚██╗██║██╔═██╗ ██╔══╝  ██║  ██║██║██║╚██╗██║{Style.RESET_ALL}",
            f"    {Fore.CYAN + Style.BRIGHT}███████╗██║██║ ╚████║██║  ██╗███████╗██████╔╝██║██║ ╚████║{Style.RESET_ALL}",
            f"    {Fore.CYAN + Style.BRIGHT}╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═══╝{Style.RESET_ALL}",
            f"",
            f"{effects[4]} {Fore.YELLOW + Style.BRIGHT}        ██████╗  ██████╗ ████████╗     █████╗ ██╗        {Style.RESET_ALL} {effects[5]}",
            f"        {Fore.YELLOW + Style.BRIGHT}██╔══██╗██╔═══██╗╚══██╔══╝    ██╔══██╗██║{Style.RESET_ALL}",
            f"        {Fore.YELLOW + Style.BRIGHT}██████╔╝██║   ██║   ██║       ███████║██║{Style.RESET_ALL}",
            f"        {Fore.YELLOW + Style.BRIGHT}██╔══██╗██║   ██║   ██║       ██╔══██║██║{Style.RESET_ALL}",
            f"        {Fore.YELLOW + Style.BRIGHT}██████╔╝╚██████╔╝   ██║       ██║  ██║██║{Style.RESET_ALL}",
            f"        {Fore.YELLOW + Style.BRIGHT}╚═════╝  ╚═════╝    ╚═╝       ╚═╝  ╚═╝╚═╝{Style.RESET_ALL}",
            f"",
            f"{effects[6]} {Fore.GREEN + Style.BRIGHT}◆═══════════════════════════════════════════════════════════════◆{Style.RESET_ALL} {effects[7]}",
            f"{Fore.GREEN + Style.BRIGHT}║           🤖 AUTOMATED LINKEDIN CONTENT MANAGEMENT 🤖           ║{Style.RESET_ALL}",
            f"{Fore.MAGENTA + Style.BRIGHT}║              ⚡ DISCORD INTEGRATION ACTIVE ⚡                  ║{Style.RESET_ALL}",
            f"{Fore.CYAN + Style.BRIGHT}║                  🚀 VERSION 2.0 - ENHANCED 🚀                  ║{Style.RESET_ALL}",
            f"{Fore.GREEN + Style.BRIGHT}◆═══════════════════════════════════════════════════════════════◆{Style.RESET_ALL}",
            f""
        ]
        
        return "\n".join(art_lines)
    
    def _show_loading_animation(self):
        """Show a brief loading animation"""
        import time
        import sys
        
        loading_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        loading_text = f"{Fore.CYAN}Initializing components"
        
        for i in range(20):  # Show animation for about 2 seconds
            char = loading_chars[i % len(loading_chars)]
            dots = '.' * ((i // 3) % 4)
            sys.stdout.write(f"\r{loading_text} {char} {dots:<3}")
            sys.stdout.flush()
            time.sleep(0.1)
        
        # Clear the loading line and show completion
        sys.stdout.write(f"\r{Fore.GREEN}✅ All components initialized successfully!{' ' * 20}\n{Style.RESET_ALL}")
        sys.stdout.flush()
    
    def connection_status(self, service: str, status: bool, details: str = None):
        """Log connection status with appropriate styling"""
        status_emoji = "✅" if status else "❌"
        status_text = "CONNECTED" if status else "FAILED"
        status_color = Fore.GREEN if status else Fore.RED
        
        if EnhancedFormatter().use_colors:
            message = f"{status_emoji} {service} connection: {status_color}{status_text}{Style.RESET_ALL}"
        else:
            message = f"{service} connection: {status_text}"
            
        if details:
            message += f" - {details}"
            
        if status:
            self.logger.info(message)
        else:
            self.logger.error(message)
    
    def api_call(self, service: str, endpoint: str, status_code: int, response_time: float = None):
        """Log API calls with status visualization"""
        status_emoji = "✅" if 200 <= status_code < 300 else "❌" if status_code >= 400 else "⚠️"
        
        message = f"{status_emoji} {service} API: {endpoint} -> {status_code}"
        
        if response_time:
            message += f" ({response_time:.2f}s)"
            
        if 200 <= status_code < 300:
            self.logger.info(message)
        elif 400 <= status_code < 500:
            self.logger.warning(message)
        else:
            self.logger.error(message)
    
    def progress_update(self, task: str, current: int, total: int):
        """Log progress updates with visual progress indication"""
        percentage = (current / total) * 100 if total > 0 else 0
        
        if EnhancedFormatter().use_colors:
            # Create a simple progress bar
            bar_length = 20
            filled = int(bar_length * percentage / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            message = f"🔄 {task}: {Fore.CYAN}{bar}{Style.RESET_ALL} {percentage:.1f}% ({current}/{total})"
        else:
            message = f"{task}: {percentage:.1f}% ({current}/{total})"
            
        self.logger.info(message)
    
    def system_health(self, component: str, status: str, metrics: Dict[str, Any] = None):
        """Log system health information"""
        status_emojis = {
            'healthy': '💚',
            'warning': '💛', 
            'critical': '❤️',
            'unknown': '💜'
        }
        
        emoji = status_emojis.get(status.lower(), '💜')
        message = f"{emoji} {component} health: {status.upper()}"
        
        if metrics:
            metric_strs = [f"{k}={v}" for k, v in metrics.items()]
            message += f" ({', '.join(metric_strs)})"
            
        if status.lower() == 'healthy':
            self.logger.info(message)
        elif status.lower() == 'warning':
            self.logger.warning(message)
        else:
            self.logger.error(message)
    
    def post_activity(self, action: str, post_id: str, details: str = None):
        """Log post-related activities"""
        action_emojis = {
            'created': '📝',
            'approved': '✅',
            'rejected': '❌',
            'published': '🚀',
            'edited': '✏️',
            'deleted': '🗑️'
        }
        
        emoji = action_emojis.get(action.lower(), '📋')
        message = f"{emoji} Post {action}: {post_id}"
        
        if details:
            message += f" - {details}"
            
        self.logger.info(message)
    
    # Standard logging methods with enhanced functionality
    def debug(self, message: str):
        self.logger.debug(message)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def critical(self, message: str):
        self.logger.critical(message)

def get_enhanced_logger(name: str) -> EnhancedLogger:
    """Get an enhanced logger instance"""
    return EnhancedLogger(name)

def setup_enhanced_logging():
    """Setup enhanced logging for the entire application"""
    # Configure root logger to use enhanced formatting
    root_logger = logging.getLogger()
    
    # Check if enhanced handler already exists
    enhanced_handler_exists = any(
        isinstance(h, logging.StreamHandler) and isinstance(h.formatter, EnhancedFormatter)
        for h in root_logger.handlers
    )
    
    if not enhanced_handler_exists:
        # Remove existing handlers
        for handler in root_logger.handlers.copy():
            root_logger.removeHandler(handler)
        
        # Add enhanced handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(EnhancedFormatter())
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
    
    # Disable duplicate logging from imported libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('discord').setLevel(logging.WARNING)

def check_dependencies():
    """Check if colorama is available and provide installation instructions"""
    if not COLORAMA_AVAILABLE:
        print("⚠️  Colorama not found. For enhanced terminal colors, install with:")
        print("   pip install colorama")
        print("   The logger will work in plain text mode.\n")
    else:
        print("✅ Enhanced logging with colors enabled\n")