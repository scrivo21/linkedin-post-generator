# LinkedIn Analytics Platform - Revised Implementation Plan (React Frontend)

**Associated Feature Branch:** `feature/linkedin-analytics`

## Executive Summary
Transform the LinkedIn Post Generator into a comprehensive internal analytics platform with a React frontend, replacing the Discord bot interface with a modern web application optimized for enterprise use.

## System Architecture Overview

```
┌─────────────────────────┐     ┌──────────────────────┐
│   React Frontend        │────▶│   FastAPI Backend    │
│   - TypeScript          │     │   - Analytics API    │
│   - Ant Design UI       │     │   - Auth/SSO         │
│   - TanStack Query      │     │   - WebSocket        │
└─────────────────────────┘     └──────────────────────┘
                                          │
                                          ▼
                              ┌──────────────────────┐
                              │   PostgreSQL         │
                              │   - Posts Data       │
                              │   - Analytics        │
                              │   - User Management  │
                              └──────────────────────┘
                                          │
                                          ▼
                              ┌──────────────────────┐
                              │   LinkedIn API       │
                              │   - OAuth 2.0        │
                              │   - Metrics API      │
                              └──────────────────────┘
```

## Phase 1: Backend Foundation (Week 1-2)

### 1.1 Comprehensive .env Configuration
Create enterprise-grade configuration with 100+ variables:

```env
# ===================================
# ENVIRONMENT CONFIGURATION
# ===================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true
CORRELATION_ID_HEADER=X-Correlation-ID

# ===================================
# DATABASE CONFIGURATION
# ===================================
DATABASE_URL=postgresql://user:pass@localhost/linkedin_analytics
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO=false
DB_SSL_MODE=prefer

# ===================================
# LINKEDIN API CONFIGURATION
# ===================================
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_PERSON_ID=your_person_id_here
LINKEDIN_API_BASE_URL=https://api.linkedin.com/rest
LINKEDIN_RATE_LIMIT_DAILY=1000
LINKEDIN_TOKEN_REFRESH_THRESHOLD=12

# ===================================
# SECURITY CONFIGURATION
# ===================================
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
API_KEY_ROTATION_DAYS=90
RATE_LIMIT_PER_MINUTE=100
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourapp.company.com
ENCRYPTION_KEY=your_encryption_key_here

# ===================================
# REDIS CACHE CONFIGURATION
# ===================================
REDIS_URL=redis://localhost:6379
REDIS_POOL_SIZE=10
REDIS_SOCKET_TIMEOUT=5
REDIS_HEALTH_CHECK_INTERVAL=30
CACHE_TTL_SECONDS=3600
QUEUE_DEFAULT_TTL=86400

# ===================================
# MONITORING & OBSERVABILITY
# ===================================
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
JAEGER_ENABLED=true
JAEGER_ENDPOINT=http://localhost:14268/api/traces
METRICS_UPDATE_ENABLED=true
METRICS_SCHEDULER_ENABLED=true

# ===================================
# FASTAPI APPLICATION
# ===================================
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true
API_ACCESS_LOG=true

# ===================================
# FEATURE FLAGS
# ===================================
ANALYTICS_ENABLED=true
REAL_TIME_METRICS=true
WEBHOOK_NOTIFICATIONS=true
API_V2_ENABLED=false
CIRCUIT_BREAKER_ENABLED=true
PWA_FEATURES_ENABLED=true

# ===================================
# SSO/AUTHENTICATION
# ===================================
SSO_PROVIDER=azure-ad
SSO_CLIENT_ID=your_sso_client_id
SSO_CLIENT_SECRET=your_sso_client_secret
SSO_TENANT_ID=your_tenant_id
SSO_REDIRECT_URI=http://localhost:3000/auth/callback

# ===================================
# EMAIL NOTIFICATIONS
# ===================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@company.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=linkedin-analytics@company.com

# ===================================
# WEBHOOK INTEGRATIONS
# ===================================
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/linkedin
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
TEAMS_WEBHOOK_URL=https://company.webhook.office.com/your/webhook

# ===================================
# EXPORT & REPORTING
# ===================================
REPORT_STORAGE_PATH=/app/reports
MAX_EXPORT_ROWS=10000
REPORT_RETENTION_DAYS=90
EXPORT_FORMATS=csv,pdf,xlsx

# ===================================
# PERFORMANCE TUNING
# ===================================
BATCH_SIZE_DEFAULT=100
MAX_CONCURRENT_REQUESTS=50
REQUEST_TIMEOUT_SECONDS=30
BULK_OPERATION_LIMIT=1000
PAGINATION_DEFAULT_SIZE=25
PAGINATION_MAX_SIZE=100

# ===================================
# DATA RETENTION
# ===================================
METRICS_RETENTION_DAYS=365
LOG_RETENTION_DAYS=30
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years
TEMP_FILE_CLEANUP_HOURS=24
```

### 1.2 Enhanced Database Schema
Update schema for analytics and React frontend:

```sql
-- ===================================
-- ANALYTICS TABLES
-- ===================================

-- Store historical metrics snapshots
CREATE TABLE linkedin_metrics_snapshots (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES linkedin_posts(id),
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metrics_data JSONB NOT NULL,
    source VARCHAR(50) DEFAULT 'api', -- 'api', 'manual', 'third_party'
    
    -- Commonly queried metrics for performance
    impressions INTEGER,
    engagement_rate DECIMAL(5,4),
    likes INTEGER,
    comments INTEGER,
    shares INTEGER,
    clicks INTEGER,
    profile_views INTEGER,
    new_followers INTEGER
);

-- Create indexes for efficient querying
CREATE INDEX idx_metrics_snapshots_post_id ON linkedin_metrics_snapshots(post_id);
CREATE INDEX idx_metrics_snapshots_captured ON linkedin_metrics_snapshots(captured_at);
CREATE INDEX idx_metrics_snapshots_engagement ON linkedin_metrics_snapshots(engagement_rate DESC);

-- Add analytics columns to existing posts table (backwards compatible)
ALTER TABLE linkedin_posts ADD COLUMN IF NOT EXISTS linkedin_urn VARCHAR(100);
ALTER TABLE linkedin_posts ADD COLUMN IF NOT EXISTS metrics JSONB DEFAULT '{}';
ALTER TABLE linkedin_posts ADD COLUMN IF NOT EXISTS metrics_summary JSONB DEFAULT '{}';
ALTER TABLE linkedin_posts ADD COLUMN IF NOT EXISTS metrics_last_updated TIMESTAMP WITH TIME ZONE;
ALTER TABLE linkedin_posts ADD COLUMN IF NOT EXISTS performance_tier VARCHAR(20);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_urn ON linkedin_posts(linkedin_urn);
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_metrics_updated ON linkedin_posts(metrics_last_updated);
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_performance ON linkedin_posts(performance_tier);

-- ===================================
-- USER MANAGEMENT TABLES
-- ===================================

-- User accounts for React application
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer', -- 'admin', 'approver', 'viewer', 'creator'
    team VARCHAR(100),
    department VARCHAR(100),
    preferences JSONB DEFAULT '{}',
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User sessions for JWT management
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Saved dashboards and custom views
CREATE TABLE saved_dashboards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL,
    is_default BOOLEAN DEFAULT false,
    is_shared BOOLEAN DEFAULT false,
    shared_with_teams TEXT[], -- Array of team names
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===================================
-- AUDIT AND COMPLIANCE
-- ===================================

-- Audit log for all user actions
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL, -- 'create', 'update', 'delete', 'approve', 'reject'
    resource_type VARCHAR(50) NOT NULL, -- 'post', 'user', 'dashboard'
    resource_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API usage tracking
CREATE TABLE api_usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===================================
-- REPORTING AND EXPORTS
-- ===================================

-- Saved reports and exports
CREATE TABLE saved_reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL, -- 'analytics', 'performance', 'audit'
    filters JSONB NOT NULL,
    schedule JSONB, -- For scheduled reports
    last_generated TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Export history
CREATE TABLE export_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    report_id INTEGER REFERENCES saved_reports(id),
    file_name VARCHAR(255) NOT NULL,
    file_format VARCHAR(10) NOT NULL, -- 'csv', 'pdf', 'xlsx'
    file_size_bytes INTEGER,
    download_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===================================
-- NOTIFICATIONS AND ALERTS
-- ===================================

-- User notification preferences
CREATE TABLE notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    email_enabled BOOLEAN DEFAULT true,
    email_frequency VARCHAR(20) DEFAULT 'immediate', -- 'immediate', 'daily', 'weekly'
    web_notifications BOOLEAN DEFAULT true,
    notification_types JSONB DEFAULT '{}', -- Which types of notifications to receive
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notification queue
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(50) NOT NULL, -- 'approval_needed', 'post_published', 'milestone_reached'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT false,
    is_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITH TIME ZONE
);
```

### 1.3 Core Services Architecture
Create modular service layer with these key components:

#### LinkedInAnalyticsService
```python
# services/linkedin_analytics_service.py
class LinkedInAnalyticsService:
    """Core analytics engine for LinkedIn metrics"""
    
    async def fetch_metrics_for_post(self, post_id: int) -> Optional[PostMetrics]
    async def bulk_update_metrics(self, post_ids: List[int]) -> Dict[str, int]
    async def get_analytics_summary(self, days: int = 30) -> Dict
    async def get_engagement_trends(self, timeframe: str) -> List[Dict]
    async def get_performance_comparison(self, post_ids: List[int]) -> Dict
    async def export_metrics_report(self, filters: Dict) -> str
```

#### AuthenticationService
```python
# services/authentication_service.py
class AuthenticationService:
    """SSO and JWT authentication management"""
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]
    async def authenticate_sso(self, sso_token: str) -> Optional[User]
    async def generate_jwt_token(self, user: User) -> str
    async def refresh_jwt_token(self, refresh_token: str) -> Optional[str]
    async def revoke_user_sessions(self, user_id: int) -> bool
```

#### DataPipelineService
```python
# services/data_pipeline_service.py
class DataPipelineService:
    """ETL and real-time data processing"""
    
    async def start_real_time_processor(self)
    async def run_etl_pipeline(self)
    async def process_metrics_batch(self, metrics_batch: List[Dict])
    async def generate_derived_metrics(self, raw_metrics: Dict) -> Dict
    async def update_materialized_views(self)
```

## Phase 2: FastAPI Backend (Week 3-4)

### 2.1 REST API Implementation
Create comprehensive API with 25+ endpoints:

```python
# API Structure
app = FastAPI(
    title="LinkedIn Analytics API",
    version="1.0.0",
    description="Internal LinkedIn Analytics Platform"
)

# ===================================
# AUTHENTICATION ENDPOINTS
# ===================================
POST   /api/auth/login              # SSO/email login
POST   /api/auth/refresh            # JWT token refresh
POST   /api/auth/logout             # Logout and revoke token
GET    /api/auth/user               # Current user profile
PUT    /api/auth/user               # Update user profile
GET    /api/auth/permissions        # User permissions

# ===================================
# POSTS MANAGEMENT
# ===================================
GET    /api/posts                   # List posts with advanced filters
POST   /api/posts                   # Create new post
GET    /api/posts/{id}              # Get specific post
PUT    /api/posts/{id}              # Update post
DELETE /api/posts/{id}              # Delete post
POST   /api/posts/{id}/approve      # Approve post
POST   /api/posts/{id}/reject       # Reject post
POST   /api/posts/bulk-approve      # Bulk approval
POST   /api/posts/bulk-reject       # Bulk rejection
GET    /api/posts/{id}/history      # Approval history
POST   /api/posts/{id}/comment      # Add comment
GET    /api/posts/{id}/comments     # Get comments

# ===================================
# ANALYTICS ENDPOINTS
# ===================================
GET    /api/analytics/overview      # Dashboard overview metrics
GET    /api/analytics/engagement    # Engagement trends over time
GET    /api/analytics/performance   # Performance metrics by category
GET    /api/analytics/top-posts     # Top performing posts
GET    /api/analytics/comparison    # Compare multiple posts
GET    /api/analytics/predictions   # Performance predictions
POST   /api/analytics/custom-query  # Custom analytics query

# ===================================
# METRICS ENDPOINTS
# ===================================
GET    /api/metrics/posts/{id}      # Detailed metrics for post
POST   /api/metrics/posts/{id}/refresh # Force metrics refresh
GET    /api/metrics/bulk            # Bulk metrics for multiple posts
GET    /api/metrics/historical      # Historical metrics data
POST   /api/metrics/export          # Export metrics data

# ===================================
# DASHBOARD & REPORTING
# ===================================
GET    /api/dashboards              # User's saved dashboards
POST   /api/dashboards              # Create new dashboard
GET    /api/dashboards/{id}         # Get dashboard config
PUT    /api/dashboards/{id}         # Update dashboard
DELETE /api/dashboards/{id}         # Delete dashboard
POST   /api/dashboards/{id}/share   # Share dashboard with team

GET    /api/reports                 # User's saved reports
POST   /api/reports                 # Create new report
POST   /api/reports/{id}/generate   # Generate report
GET    /api/reports/{id}/download   # Download generated report

# ===================================
# USER MANAGEMENT
# ===================================
GET    /api/users                   # List users (admin only)
POST   /api/users                   # Create user (admin only)
GET    /api/users/{id}              # Get user details
PUT    /api/users/{id}              # Update user
DELETE /api/users/{id}              # Deactivate user
GET    /api/users/{id}/activity     # User activity log

# ===================================
# NOTIFICATIONS
# ===================================
GET    /api/notifications           # User notifications
POST   /api/notifications/{id}/read # Mark notification as read
PUT    /api/notifications/preferences # Update notification preferences
POST   /api/notifications/test      # Send test notification

# ===================================
# ADMIN ENDPOINTS
# ===================================
GET    /api/admin/stats             # System statistics
GET    /api/admin/health            # System health check
GET    /api/admin/logs              # Application logs
POST   /api/admin/maintenance       # Maintenance mode toggle
GET    /api/admin/audit             # Audit logs

# ===================================
# REAL-TIME WEBSOCKETS
# ===================================
WS     /ws/metrics                  # Live metrics updates
WS     /ws/notifications            # Real-time notifications
WS     /ws/posts                    # Post status updates
WS     /ws/dashboard/{id}           # Dashboard live updates
```

### 2.2 LinkedIn API Integration
Implement robust LinkedIn integration with:

```python
# linkedin_api/client.py
class LinkedInAPIClient:
    """Enhanced LinkedIn API client with OAuth 2.0"""
    
    def __init__(self):
        self.token_manager = LinkedInTokenManager()
        self.rate_limiter = DistributedRateLimiter()
        self.circuit_breaker = CircuitBreaker()
        
    async def get_post_metrics(self, urn: str) -> Dict[str, Any]:
        """Fetch metrics using Member Post Analytics API"""
        
    async def bulk_get_metrics(self, urns: List[str]) -> List[Dict[str, Any]]:
        """Batch fetch metrics for multiple posts"""
        
    async def publish_post(self, content: str, **kwargs) -> str:
        """Publish post to LinkedIn"""
        
    async def get_profile_info(self) -> Dict[str, Any]:
        """Get user profile information"""
```

### 2.3 Security Implementation

```python
# security/auth.py
class SecurityManager:
    """Comprehensive security management"""
    
    def __init__(self):
        self.jwt_manager = JWTManager()
        self.rate_limiter = RateLimiter()
        self.audit_logger = AuditLogger()
        
    async def authenticate_request(self, request: Request) -> Optional[User]:
        """Authenticate API request"""
        
    async def check_permissions(self, user: User, resource: str, action: str) -> bool:
        """Check RBAC permissions"""
        
    async def log_security_event(self, event_type: str, user_id: int, details: Dict):
        """Log security events for audit"""
```

## Phase 3: React Frontend Development (Week 5-7)

### 3.1 Project Setup
Initialize modern React application:

```bash
# Create React app with Vite
npm create vite@latest linkedin-analytics-frontend -- --template react-ts

# Core dependencies
npm install antd @tanstack/react-query zustand axios react-router-dom
npm install recharts date-fns react-hook-form @hookform/resolvers/zod zod
npm install @types/react @types/node @types/react-dom -D

# Development dependencies
npm install @vitejs/plugin-react typescript vite -D
npm install eslint @typescript-eslint/eslint-plugin @typescript-eslint/parser -D
npm install prettier eslint-config-prettier eslint-plugin-prettier -D
npm install vitest @testing-library/react @testing-library/jest-dom -D
```

### 3.2 Application Structure
```
src/
├── components/
│   ├── ui/                     # Basic UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Modal.tsx
│   │   └── index.ts
│   ├── layout/                 # Layout components
│   │   ├── AppLayout.tsx
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   ├── charts/                 # Chart components
│   │   ├── EngagementChart.tsx
│   │   ├── PerformanceChart.tsx
│   │   ├── HeatMap.tsx
│   │   └── MetricsCard.tsx
│   └── forms/                  # Form components
│       ├── PostForm.tsx
│       ├── FilterForm.tsx
│       └── SearchForm.tsx
├── features/
│   ├── auth/
│   │   ├── components/
│   │   │   ├── LoginForm.tsx
│   │   │   └── UserProfile.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── usePermissions.ts
│   │   └── services/
│   │       └── authService.ts
│   ├── posts/
│   │   ├── components/
│   │   │   ├── PostList.tsx
│   │   │   ├── PostCard.tsx
│   │   │   ├── PostDetail.tsx
│   │   │   ├── PostCreator.tsx
│   │   │   ├── ApprovalQueue.tsx
│   │   │   └── BulkActions.tsx
│   │   ├── hooks/
│   │   │   ├── usePosts.ts
│   │   │   ├── usePostMetrics.ts
│   │   │   └── useApproval.ts
│   │   └── services/
│   │       └── postsService.ts
│   ├── analytics/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── EngagementDashboard.tsx
│   │   │   ├── PerformanceDashboard.tsx
│   │   │   ├── CustomDashboard.tsx
│   │   │   └── ReportBuilder.tsx
│   │   ├── hooks/
│   │   │   ├── useAnalytics.ts
│   │   │   ├── useDashboard.ts
│   │   │   └── useReports.ts
│   │   └── services/
│   │       └── analyticsService.ts
│   └── admin/
│       ├── components/
│       │   ├── UserManagement.tsx
│       │   ├── SystemHealth.tsx
│       │   └── AuditLogs.tsx
│       └── hooks/
│           └── useAdmin.ts
├── hooks/
│   ├── useWebSocket.ts         # WebSocket connection hook
│   ├── useLocalStorage.ts      # Local storage hook
│   ├── useDebounce.ts          # Debounce hook
│   └── useNotifications.ts     # Notifications hook
├── services/
│   ├── api.ts                  # Main API client
│   ├── websocket.ts            # WebSocket client
│   ├── notifications.ts        # Notification service
│   └── storage.ts              # Local storage service
├── stores/
│   ├── authStore.ts            # Authentication state
│   ├── uiStore.ts              # UI state (theme, sidebar)
│   └── notificationStore.ts    # Notifications state
├── types/
│   ├── api.ts                  # API response types
│   ├── post.ts                 # Post-related types
│   ├── user.ts                 # User-related types
│   └── analytics.ts            # Analytics types
├── utils/
│   ├── dateUtils.ts            # Date formatting utilities
│   ├── formatUtils.ts          # Data formatting utilities
│   ├── validationUtils.ts      # Form validation utilities
│   └── constants.ts            # Application constants
├── pages/
│   ├── DashboardPage.tsx
│   ├── PostsPage.tsx
│   ├── AnalyticsPage.tsx
│   ├── ReportsPage.tsx
│   ├── SettingsPage.tsx
│   └── AdminPage.tsx
├── styles/
│   ├── globals.css
│   ├── antd-theme.ts           # Ant Design theme customization
│   └── variables.css
├── App.tsx
├── main.tsx
└── vite-env.d.ts
```

### 3.3 Key Features Implementation

#### Main Dashboard Component
```typescript
// features/analytics/components/Dashboard.tsx
interface DashboardProps {
  user: User;
  timeRange: TimeRange;
}

export const Dashboard: React.FC<DashboardProps> = ({ user, timeRange }) => {
  const { data: overview } = useAnalyticsOverview(timeRange);
  const { data: recentPosts } = useRecentPosts();
  const { data: pendingApprovals } = usePendingApprovals();

  return (
    <div className="dashboard">
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <MetricsOverview data={overview} />
        </Col>
        
        <Col span={16}>
          <Card title="Engagement Trends">
            <EngagementChart data={overview?.engagement_trends} />
          </Card>
        </Col>
        
        <Col span={8}>
          <Card title="Pending Approvals" extra={<Badge count={pendingApprovals?.length} />}>
            <ApprovalQueue posts={pendingApprovals} compact />
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Top Performing Posts">
            <TopPostsList posts={overview?.top_posts} />
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Recent Activity">
            <ActivityFeed posts={recentPosts} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
```

#### Post Management with Approval Workflow
```typescript
// features/posts/components/ApprovalQueue.tsx
interface ApprovalQueueProps {
  teamId?: string;
  compact?: boolean;
}

export const ApprovalQueue: React.FC<ApprovalQueueProps> = ({ teamId, compact }) => {
  const { data: pendingPosts, isLoading } = usePendingPosts(teamId);
  const approveMutation = useOptimisticApproval();
  const rejectMutation = useOptimisticRejection();
  const [selectedPosts, setSelectedPosts] = useState<string[]>([]);

  const handleBulkApprove = async () => {
    await approveMutation.mutateAsync(selectedPosts);
    setSelectedPosts([]);
    message.success(`Approved ${selectedPosts.length} posts`);
  };

  return (
    <div className="approval-queue">
      {!compact && (
        <div className="queue-header">
          <Space>
            <Select placeholder="Filter by status" style={{ width: 150 }}>
              <Option value="pending">Pending</Option>
              <Option value="approved">Approved</Option>
              <Option value="rejected">Rejected</Option>
            </Select>
            
            <RangePicker placeholder={['Start Date', 'End Date']} />
            
            <Button 
              type="primary" 
              disabled={selectedPosts.length === 0}
              onClick={handleBulkApprove}
            >
              Bulk Approve ({selectedPosts.length})
            </Button>
          </Space>
        </div>
      )}

      <List
        loading={isLoading}
        dataSource={pendingPosts}
        renderItem={(post) => (
          <PostCard
            key={post.id}
            post={post}
            selectable
            selected={selectedPosts.includes(post.id)}
            onSelect={(postId) => {
              setSelectedPosts(prev => 
                prev.includes(postId) 
                  ? prev.filter(id => id !== postId)
                  : [...prev, postId]
              );
            }}
            actions={[
              <Button 
                type="primary" 
                icon={<CheckOutlined />}
                onClick={() => approveMutation.mutate([post.id])}
                loading={approveMutation.isLoading}
              >
                Approve
              </Button>,
              <Button 
                danger 
                icon={<CloseOutlined />}
                onClick={() => rejectMutation.mutate([post.id])}
                loading={rejectMutation.isLoading}
              >
                Reject
              </Button>
            ]}
          />
        )}
      />
    </div>
  );
};
```

#### Advanced Analytics Dashboard
```typescript
// features/analytics/components/AnalyticsDashboard.tsx
export const AnalyticsDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');
  const [filters, setFilters] = useState<AnalyticsFilters>({});
  
  const { data: metrics } = useAnalyticsMetrics(timeRange, filters);
  const { data: trends } = useEngagementTrends(timeRange);
  const { data: comparison } = usePerformanceComparison(filters);

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-controls">
        <Space>
          <Select value={timeRange} onChange={setTimeRange}>
            <Option value="7d">Last 7 days</Option>
            <Option value="30d">Last 30 days</Option>
            <Option value="90d">Last 90 days</Option>
            <Option value="1y">Last year</Option>
          </Select>
          
          <FilterDrawer filters={filters} onFiltersChange={setFilters} />
          
          <Button icon={<ExportOutlined />} onClick={() => exportDashboard()}>
            Export
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        <Col span={24}>
          <MetricsCards metrics={metrics?.summary} />
        </Col>
        
        <Col span={16}>
          <Card title="Engagement Over Time">
            <EngagementChart data={trends} />
          </Card>
        </Col>
        
        <Col span={8}>
          <Card title="Performance Distribution">
            <PerformancePieChart data={comparison?.distribution} />
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Best Posting Times">
            <PostingHeatMap data={metrics?.posting_times} />
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Content Performance">
            <ContentAnalysisChart data={metrics?.content_analysis} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
```

### 3.4 Real-time Features with WebSocket
```typescript
// hooks/useWebSocket.ts
export const useWebSocket = (url: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setIsConnected(true);
      setSocket(ws);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      setSocket(null);
    };
    
    return () => {
      ws.close();
    };
  }, [url]);

  const sendMessage = useCallback((message: any) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(message));
    }
  }, [socket, isConnected]);

  return { socket, isConnected, sendMessage };
};

// Real-time metrics updates
export const useRealTimeMetrics = () => {
  const queryClient = useQueryClient();
  const { socket } = useWebSocket(`${WS_BASE_URL}/ws/metrics`);

  useEffect(() => {
    if (!socket) return;

    socket.onmessage = (event) => {
      const update = JSON.parse(event.data);
      
      // Update specific post metrics
      queryClient.setQueryData(['posts', update.post_id], (old: Post) => ({
        ...old,
        metrics: update.metrics
      }));
      
      // Update analytics overview
      queryClient.invalidateQueries(['analytics', 'overview']);
    };
  }, [socket, queryClient]);
};
```

## Phase 4: Data Pipeline & ETL (Week 8)

### 4.1 Real-time Processing Architecture
```python
# data_pipeline/real_time_processor.py
class RealTimeMetricsProcessor:
    """Process real-time LinkedIn metrics updates"""
    
    def __init__(self):
        self.redis_client = redis.Redis()
        self.websocket_manager = WebSocketManager()
        self.notification_service = NotificationService()
    
    async def process_metrics_update(self, post_id: int, metrics: Dict):
        """Process incoming metrics update"""
        
        # Update database
        await self.store_metrics_update(post_id, metrics)
        
        # Check for milestones
        milestones = await self.check_milestones(post_id, metrics)
        
        # Broadcast to connected clients
        await self.websocket_manager.broadcast({
            'type': 'metrics_update',
            'post_id': post_id,
            'metrics': metrics,
            'milestones': milestones
        })
        
        # Send notifications for milestones
        for milestone in milestones:
            await self.notification_service.send_milestone_notification(
                post_id, milestone, metrics
            )
    
    async def check_milestones(self, post_id: int, metrics: Dict) -> List[str]:
        """Check if post hit any performance milestones"""
        milestones = []
        
        impressions = metrics.get('impressions', 0)
        engagement_rate = metrics.get('engagement_rate', 0)
        
        if impressions >= 10000:
            milestones.append('10k_impressions')
        if impressions >= 100000:
            milestones.append('100k_impressions')
        if engagement_rate >= 0.05:
            milestones.append('viral_performance')
        
        return milestones
```

### 4.2 ETL Pipeline Implementation
```python
# data_pipeline/etl_processor.py
class MetricsETLProcessor:
    """Extract, Transform, Load pipeline for metrics data"""
    
    async def run_etl_pipeline(self):
        """Run complete ETL pipeline"""
        
        # Extract: Get raw metrics from LinkedIn API
        raw_metrics = await self.extract_metrics()
        
        # Transform: Process and enrich data
        transformed_metrics = await self.transform_metrics(raw_metrics)
        
        # Load: Store in data warehouse
        await self.load_metrics(transformed_metrics)
        
        # Update materialized views
        await self.refresh_materialized_views()
    
    async def extract_metrics(self) -> List[Dict]:
        """Extract metrics from LinkedIn API"""
        posts_needing_update = await self.get_posts_for_update()
        metrics_batch = []
        
        for post in posts_needing_update:
            try:
                metrics = await self.linkedin_api.get_post_metrics(post.linkedin_urn)
                metrics_batch.append({
                    'post_id': post.id,
                    'urn': post.linkedin_urn,
                    'raw_metrics': metrics,
                    'extracted_at': datetime.utcnow()
                })
            except Exception as e:
                logger.error(f"Failed to extract metrics for post {post.id}: {e}")
        
        return metrics_batch
    
    async def transform_metrics(self, raw_metrics: List[Dict]) -> List[Dict]:
        """Transform raw metrics into standardized format"""
        transformed = []
        
        for item in raw_metrics:
            raw = item['raw_metrics']
            
            # Calculate derived metrics
            total_engagement = raw.get('likes', 0) + raw.get('comments', 0) + raw.get('shares', 0)
            engagement_rate = total_engagement / max(raw.get('impressions', 1), 1)
            
            # Determine performance tier
            performance_tier = self.calculate_performance_tier(engagement_rate)
            
            # Add time-based features
            hour_of_day = item['extracted_at'].hour
            day_of_week = item['extracted_at'].weekday()
            
            transformed_item = {
                'post_id': item['post_id'],
                'urn': item['urn'],
                'extracted_at': item['extracted_at'],
                
                # Raw metrics
                'impressions': raw.get('impressions', 0),
                'unique_impressions': raw.get('unique_impressions', 0),
                'likes': raw.get('likes', 0),
                'comments': raw.get('comments', 0),
                'shares': raw.get('shares', 0),
                'clicks': raw.get('clicks', 0),
                'profile_views': raw.get('profile_views', 0),
                'new_followers': raw.get('new_followers', 0),
                
                # Derived metrics
                'total_engagement': total_engagement,
                'engagement_rate': engagement_rate,
                'performance_tier': performance_tier,
                'ctr': raw.get('clicks', 0) / max(raw.get('impressions', 1), 1),
                
                # Time features
                'hour_of_day': hour_of_day,
                'day_of_week': day_of_week,
                'is_weekend': day_of_week >= 5,
                
                # Full raw data for future analysis
                'raw_data': raw
            }
            
            transformed.append(transformed_item)
        
        return transformed
    
    def calculate_performance_tier(self, engagement_rate: float) -> str:
        """Categorize post performance"""
        if engagement_rate >= 0.05:
            return "viral"
        elif engagement_rate >= 0.03:
            return "high"
        elif engagement_rate >= 0.015:
            return "medium"
        elif engagement_rate >= 0.005:
            return "low"
        else:
            return "minimal"
```

## Phase 5: Monitoring & DevOps (Week 9)

### 5.1 Docker Configuration

#### Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash analytics
RUN chown -R analytics:analytics /app
USER analytics

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose ports
EXPOSE 8000 9090

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8000
    depends_on:
      - backend
    networks:
      - linkedin-analytics

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
      - "9090:9090"  # Prometheus metrics
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/linkedin_analytics
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
      - ./exports:/app/exports
    networks:
      - linkedin-analytics

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: linkedin_analytics
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - linkedin-analytics

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - linkedin-analytics

  # Monitoring stack
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9091:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - linkedin-analytics

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - linkedin-analytics

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - linkedin-analytics

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    networks:
      - linkedin-analytics

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  linkedin-analytics:
    driver: bridge
```

### 5.2 Monitoring Configuration

#### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'linkedin-analytics-backend'
    static_configs:
      - targets: ['backend:9090']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "title": "LinkedIn Analytics Platform",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(linkedin_api_request_duration_seconds_bucket[5m])) by (le))"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "count(linkedin_active_sessions)"
          }
        ]
      },
      {
        "title": "Posts Processing Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(linkedin_posts_processed_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## Phase 6: Testing & Deployment (Week 10)

### 6.1 Testing Strategy

#### Backend Testing
```python
# tests/test_analytics_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from services.linkedin_analytics_service import LinkedInAnalyticsService

class TestLinkedInAnalyticsService:
    @pytest.fixture
    async def analytics_service(self):
        db_mock = AsyncMock()
        api_mock = AsyncMock()
        config_mock = Mock()
        
        return LinkedInAnalyticsService(db_mock, api_mock, config_mock)
    
    @pytest.mark.asyncio
    async def test_fetch_metrics_success(self, analytics_service):
        # Mock successful API response
        analytics_service.db.fetchrow.return_value = {
            'id': 1, 
            'linkedin_urn': 'urn:li:share:123456'
        }
        
        analytics_service.linkedin_api.get_post_metrics.return_value = {
            'impressions': 1000,
            'likes': 50,
            'comments': 10,
            'shares': 5
        }
        
        metrics = await analytics_service.fetch_metrics_for_post(1)
        
        assert metrics is not None
        assert metrics.post_id == 1
        assert metrics.impressions == 1000
        assert metrics.engagement_rate > 0
    
    @pytest.mark.asyncio
    async def test_bulk_update_rate_limiting(self, analytics_service):
        post_ids = list(range(1, 25))  # 24 posts
        
        analytics_service.fetch_metrics_for_post = AsyncMock(
            return_value=Mock()
        )
        
        result = await analytics_service.bulk_update_metrics(post_ids)
        
        assert result["success"] == 24
        assert result["failed"] == 0
```

#### Frontend Testing
```typescript
// src/features/posts/components/__tests__/PostCard.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PostCard } from '../PostCard';

const mockPost = {
  id: '1',
  content: 'Test post content',
  status: 'pending',
  metrics: {
    impressions: 1000,
    engagement_rate: 0.05
  }
};

describe('PostCard', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    });
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  it('renders post content correctly', () => {
    renderWithProviders(
      <PostCard post={mockPost} onApprove={jest.fn()} onReject={jest.fn()} />
    );

    expect(screen.getByText('Test post content')).toBeInTheDocument();
    expect(screen.getByText('1,000')).toBeInTheDocument(); // Impressions
    expect(screen.getByText('5.00%')).toBeInTheDocument(); // Engagement rate
  });

  it('calls onApprove when approve button is clicked', async () => {
    const onApprove = jest.fn();
    
    renderWithProviders(
      <PostCard post={mockPost} onApprove={onApprove} onReject={jest.fn()} />
    );

    fireEvent.click(screen.getByRole('button', { name: /approve/i }));
    
    await waitFor(() => {
      expect(onApprove).toHaveBeenCalledWith(mockPost.id);
    });
  });
});
```

#### E2E Testing
```typescript
// e2e/approval-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Approval Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid=email]', 'test@company.com');
    await page.fill('[data-testid=password]', 'password');
    await page.click('[data-testid=login-button]');
    await page.waitForURL('/dashboard');
  });

  test('should approve post successfully', async ({ page }) => {
    // Navigate to approval queue
    await page.click('[data-testid=approval-queue-link]');
    
    // Find first pending post
    const firstPost = page.locator('[data-testid=post-card]').first();
    await expect(firstPost).toBeVisible();
    
    // Click approve button
    await firstPost.locator('[data-testid=approve-button]').click();
    
    // Check for success message
    await expect(page.locator('.ant-message-success')).toBeVisible();
    
    // Verify post is no longer in pending queue
    await expect(firstPost).not.toBeVisible();
  });

  test('should handle bulk approval', async ({ page }) => {
    await page.goto('/posts/approval');
    
    // Select multiple posts
    await page.check('[data-testid=post-checkbox-1]');
    await page.check('[data-testid=post-checkbox-2]');
    
    // Click bulk approve
    await page.click('[data-testid=bulk-approve-button]');
    
    // Confirm action
    await page.click('[data-testid=confirm-bulk-approve]');
    
    // Check success message
    await expect(page.locator('.ant-message-success')).toContainText('Approved 2 posts');
  });
});
```

### 6.2 Deployment Configuration

#### CI/CD Pipeline
```yaml
# .github/workflows/ci-cd.yml
name: LinkedIn Analytics CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      working-directory: ./backend
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      working-directory: ./backend
      run: |
        flake8 . --max-line-length=100
        black --check .
        isort --check-only .
    
    - name: Run type checking
      working-directory: ./backend
      run: mypy .
    
    - name: Run tests
      working-directory: ./backend
      env:
        DATABASE_URL: postgresql://postgres:test@localhost/test
        REDIS_URL: redis://localhost:6379
        ENVIRONMENT: test
      run: |
        pytest --cov=. --cov-report=xml --cov-report=html
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: ./frontend/package-lock.json
    
    - name: Install dependencies
      working-directory: ./frontend
      run: npm ci
    
    - name: Run linting
      working-directory: ./frontend
      run: |
        npm run lint
        npm run type-check
    
    - name: Run tests
      working-directory: ./frontend
      run: npm run test:coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd frontend && npm ci
        cd ../backend && pip install -r requirements.txt
    
    - name: Start services
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30  # Wait for services to be ready
    
    - name: Run E2E tests
      run: |
        cd frontend
        npx playwright test
    
    - name: Upload E2E results
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: playwright-results
        path: frontend/test-results/

  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run backend security scan
      working-directory: ./backend
      run: |
        pip install safety bandit
        safety check
        bandit -r . -f json -o bandit-report.json
    
    - name: Run frontend security scan
      working-directory: ./frontend
      run: |
        npm audit --audit-level moderate
        npx eslint . --ext .ts,.tsx --max-warnings 0
    
    - name: Upload security results
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          backend/bandit-report.json
          frontend/eslint-report.json

  build-and-deploy:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend, e2e-tests, security-scan]
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker images
      run: |
        docker build -t linkedin-analytics-backend ./backend
        docker build -t linkedin-analytics-frontend ./frontend
    
    - name: Deploy to staging
      if: github.ref == 'refs/heads/develop'
      run: |
        # Deploy to staging environment
        echo "Deploying to staging..."
    
    - name: Deploy to production
      if: github.ref == 'refs/heads/main'
      run: |
        # Deploy to production environment
        echo "Deploying to production..."
```

#### Production Deployment Script
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "🚀 Deploying LinkedIn Analytics Platform..."

# Load environment variables
source .env.production

# Backup current database
echo "📊 Creating database backup..."
pg_dump $DATABASE_URL > "backups/backup_$(date +%Y%m%d_%H%M%S).sql"

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose pull

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose run --rm backend python -m alembic upgrade head

# Start services with zero downtime
echo "⚡ Starting services..."
docker-compose up -d --remove-orphans

# Wait for health checks
echo "🔍 Waiting for services to be healthy..."
timeout 300 bash -c '
  until docker-compose exec backend curl -f http://localhost:8000/api/health; do
    echo "Waiting for backend..."
    sleep 5
  done
'

timeout 300 bash -c '
  until docker-compose exec frontend curl -f http://localhost:80; do
    echo "Waiting for frontend..."
    sleep 5
  done
'

# Run post-deployment tests
echo "🧪 Running post-deployment tests..."
docker-compose exec backend python -m pytest tests/health/
docker-compose exec frontend npm run test:smoke

# Clean up old images
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Deployment complete!"
echo "📊 Backend API: https://api.yourcompany.com"
echo "🌐 Frontend: https://linkedin-analytics.yourcompany.com"
echo "📈 Grafana: https://grafana.yourcompany.com"
echo "🔍 Jaeger: https://jaeger.yourcompany.com"
```

## Key Files to Create/Modify

### New Files to Create

#### Backend Files
1. **`.env.example`** - Comprehensive environment configuration template
2. **`backend/main.py`** - FastAPI application entry point
3. **`backend/core/config.py`** - Enhanced configuration management
4. **`backend/core/security.py`** - Authentication and authorization
5. **`backend/services/linkedin_analytics.py`** - Core analytics service
6. **`backend/services/auth.py`** - Authentication service
7. **`backend/api/routes/`** - API endpoint modules
8. **`backend/models/`** - Enhanced database models
9. **`backend/schemas/`** - Pydantic request/response schemas
10. **`backend/data_pipeline/`** - ETL and real-time processing

#### Frontend Files
1. **`frontend/src/App.tsx`** - Main React application
2. **`frontend/src/features/`** - Feature-based modules
3. **`frontend/src/services/api.ts`** - API client service
4. **`frontend/src/stores/`** - Zustand state management
5. **`frontend/src/components/`** - Reusable UI components
6. **`frontend/src/hooks/`** - Custom React hooks
7. **`frontend/vite.config.ts`** - Vite configuration
8. **`frontend/tailwind.config.js`** - Tailwind CSS configuration

#### Infrastructure Files
1. **`docker-compose.yml`** - Multi-service container orchestration
2. **`backend/Dockerfile`** - Backend container configuration
3. **`frontend/Dockerfile`** - Frontend container configuration
4. **`nginx/nginx.conf`** - Reverse proxy configuration
5. **`monitoring/prometheus.yml`** - Metrics collection configuration
6. **`monitoring/grafana/`** - Dashboard configurations
7. **`.github/workflows/ci-cd.yml`** - CI/CD pipeline

### Modified Files
1. **`schema.sql`** - Enhanced database schema with analytics tables
2. **`requirements.txt`** - Updated Python dependencies
3. **`frontend/package.json`** - React application dependencies

## Migration Strategy

### From Discord Bot to React App
1. **Database Compatibility**: All new tables and columns are additive, maintaining existing schema
2. **Data Preservation**: Existing posts, approvals, and user data remain intact
3. **Feature Mapping**: Discord commands become web UI actions
4. **User Migration**: Map Discord users to web application accounts
5. **Notification System**: Replace Discord messages with web notifications and email

### Migration Steps
```sql
-- 1. Create new user accounts from Discord data
INSERT INTO users (email, name, role, team)
SELECT 
    discord_username || '@company.com' as email,
    discord_display_name as name,
    CASE 
        WHEN is_admin THEN 'admin'
        WHEN can_approve THEN 'approver'
        ELSE 'viewer'
    END as role,
    team_name as team
FROM discord_users;

-- 2. Link existing posts to new user accounts
UPDATE linkedin_posts 
SET created_by_user_id = (
    SELECT id FROM users 
    WHERE email = created_by_discord || '@company.com'
)
WHERE created_by_discord IS NOT NULL;

-- 3. Migrate approval history
UPDATE linkedin_posts 
SET approved_by_user_id = (
    SELECT id FROM users 
    WHERE email = approved_by_discord || '@company.com'
)
WHERE approved_by_discord IS NOT NULL;
```

## Success Metrics

### Performance Targets
- **Page Load Time**: < 2 seconds for initial load
- **API Response Time**: < 200ms (p95) for standard operations
- **Database Query Time**: < 50ms (p95) for analytics queries
- **Real-time Update Latency**: < 3 seconds for WebSocket updates
- **Concurrent Users**: Support 100+ simultaneous users
- **Uptime**: 99.9% availability SLA

### Business Metrics
- **User Adoption**: 90%+ of team using web interface within 30 days
- **Approval Efficiency**: 50% reduction in time from post creation to approval
- **Analytics Usage**: 80%+ of users accessing analytics dashboard weekly
- **Mobile Usage**: 30%+ of users accessing via mobile devices
- **Export Usage**: 50%+ of managers using export features monthly

### Technical Metrics
- **Test Coverage**: 80%+ backend coverage, 70%+ frontend coverage
- **Security Compliance**: Zero high/critical vulnerabilities
- **Performance Monitoring**: All key metrics tracked and alerted
- **Data Accuracy**: 99%+ accuracy in LinkedIn metrics synchronization
- **Error Rate**: < 1% error rate for all API endpoints

## Advantages of React Over Discord Bot

### User Experience
- **Professional Interface**: Modern, responsive web application
- **Rich Visualizations**: Interactive charts and dashboards
- **Better Navigation**: Intuitive menu structure and search
- **Mobile Support**: Fully responsive design for all devices
- **Offline Capability**: PWA features for limited offline access

### Functionality
- **Advanced Analytics**: Complex data visualizations and custom reports
- **Bulk Operations**: Efficient handling of multiple posts
- **Custom Dashboards**: Personalized views per user/team
- **Export Capabilities**: PDF, CSV, and Excel report generation
- **Search & Filtering**: Powerful search with multiple filter options

### Integration
- **SSO Integration**: Seamless corporate authentication
- **Role-Based Access**: Granular permission management
- **API Integration**: RESTful API for future integrations
- **Webhook Support**: External system notifications
- **Real-time Updates**: Live metrics and notifications

### Scalability
- **Concurrent Users**: Support for 100+ simultaneous users
- **Performance**: Optimized for large datasets and high traffic
- **Monitoring**: Comprehensive observability and alerting
- **Deployment**: Docker-based infrastructure for easy scaling
- **Maintenance**: Automated updates and monitoring

This comprehensive plan transforms the LinkedIn Post Generator into a modern, scalable, and feature-rich analytics platform optimized for internal enterprise use while maintaining all existing functionality and providing a clear migration path.