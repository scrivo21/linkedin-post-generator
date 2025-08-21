# Native iOS/macOS LinkedIn Manager App Implementation Plan

## Executive Summary

This document provides a comprehensive roadmap for transforming the existing Discord bot LinkedIn Post Generator system into a native iOS and macOS application using SwiftUI frontend with Python FastAPI backend service.

### Current System Overview
- Python Discord bot managing LinkedIn post approval workflow
- PostgreSQL database for post storage and status tracking
- LinkedIn API integration for publishing
- HTML web application for post creation
- Real-time monitoring and approval via Discord reactions

### Target Architecture
- Native SwiftUI applications for iOS and macOS
- Python FastAPI backend service with WebSocket support
- Apple Push Notification Service replacing Discord notifications
- Universal app with platform-specific features
- Offline capability with intelligent synchronization

---

## 1. Backend API Architecture

### 1.1 FastAPI Service Structure

```
api/
├── main.py                 # FastAPI app initialization
├── routers/
│   ├── posts.py           # Post CRUD operations
│   ├── auth.py            # Authentication endpoints
│   ├── approvals.py       # Approval workflow
│   ├── publishing.py      # LinkedIn publishing
│   └── websocket.py       # Real-time updates
├── services/
│   ├── database.py        # Database operations
│   ├── linkedin.py        # LinkedIn API wrapper
│   ├── notifications.py   # Push notification service
│   └── mockup.py          # Preview generation
├── models/
│   ├── post.py            # Pydantic models
│   ├── user.py            # User authentication
│   └── responses.py       # API responses
├── middleware/
│   ├── auth.py            # JWT validation
│   └── rate_limit.py      # Rate limiting
└── core/
    ├── config.py          # Configuration management
    └── security.py        # Security utilities
```

### 1.2 Complete API Endpoints

#### Authentication
```
POST   /api/auth/login          # Device authentication
POST   /api/auth/refresh         # Token refresh
POST   /api/auth/device/register # Register device for push
DELETE /api/auth/logout          # Logout and invalidate tokens
```

#### Posts Management
```
GET    /api/posts                # List all posts (paginated)
POST   /api/posts                # Create new post
GET    /api/posts/{id}           # Get specific post
PUT    /api/posts/{id}           # Update post
DELETE /api/posts/{id}           # Delete post
GET    /api/posts/stats          # Get post statistics
```

#### Approval Workflow
```
GET    /api/posts/pending        # Get pending approval posts
GET    /api/posts/approved       # Get approved posts
GET    /api/posts/published      # Get published posts
POST   /api/approvals/{id}/approve  # Approve post
POST   /api/approvals/{id}/reject   # Reject post
POST   /api/approvals/{id}/edit     # Request edit
GET    /api/approvals/history    # Get approval history
```

#### Publishing
```
POST   /api/publish/{id}         # Publish to LinkedIn
GET    /api/publish/{id}/status  # Check publish status
POST   /api/publish/{id}/schedule # Schedule for later publishing
DELETE /api/publish/{id}/cancel  # Cancel scheduled post
```

#### Utilities
```
GET    /api/mockup/{id}          # Generate LinkedIn preview
POST   /api/mockup/generate      # Generate from content
GET    /api/health               # Health check endpoint
WS     /ws/updates              # WebSocket for real-time updates
```

### 1.3 Request/Response Schemas

#### Post Model
```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PostStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    FAILED = "failed"

class PostCreate(BaseModel):
    content: str
    industry: Optional[str] = None
    audience: Optional[str] = None
    golden_threads: Optional[str] = None
    image_url: Optional[str] = None
    scheduled_for: Optional[datetime] = None

class PostResponse(BaseModel):
    id: str
    content: str
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime]
    published_at: Optional[datetime]
    industry: Optional[str]
    audience: Optional[str]
    golden_threads: Optional[str]
    image_url: Optional[str]
    linkedin_url: Optional[str]
    approval_count: int = 0
    rejection_reason: Optional[str]
```

### 1.4 Authentication Strategy

#### JWT Implementation
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_device(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        device_id: str = payload.get("device_id")
        if device_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return device_id
```

### 1.5 WebSocket Implementation

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                await self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

## 2. SwiftUI Application Architecture

### 2.1 Project Structure

```
LinkedInManager/
├── LinkedInManagerApp.swift                    # App entry point
├── iOS/
│   ├── Views/
│   │   ├── ContentView.swift                  # Main iOS view
│   │   ├── PostList/
│   │   │   ├── PostListView.swift             # Main list view
│   │   │   ├── PostRowView.swift              # Individual post row
│   │   │   ├── PostFilterBar.swift            # Filter controls
│   │   │   └── PullToRefreshView.swift        # Custom refresh control
│   │   ├── PostDetail/
│   │   │   ├── PostDetailView.swift           # Detailed post view
│   │   │   ├── ApprovalActionsView.swift      # Approve/reject buttons
│   │   │   ├── LinkedInPreviewView.swift      # Post preview
│   │   │   └── EditRequestSheet.swift         # Edit request form
│   │   ├── CreatePost/
│   │   │   ├── CreatePostView.swift           # Post creation form
│   │   │   ├── IndustryPickerView.swift       # Industry selection
│   │   │   ├── AudienceInputView.swift        # Target audience input
│   │   │   ├── GoldenThreadsView.swift        # Theme selection
│   │   │   └── PostPreviewView.swift          # Live preview
│   │   ├── Settings/
│   │   │   ├── SettingsView.swift             # App settings
│   │   │   ├── NotificationSettingsView.swift # Push notification prefs
│   │   │   └── AccountView.swift              # Account management
│   │   └── Authentication/
│   │       ├── WelcomeView.swift              # First launch
│   │       ├── DeviceRegistrationView.swift   # Device setup
│   │       └── BiometricAuthView.swift        # Face ID/Touch ID
│   ├── Widgets/
│   │   ├── PendingPostsWidget.swift           # Home screen widget
│   │   └── PostStatsWidget.swift             # Statistics widget
│   └── Extensions/
│       └── ShareExtension/
│           ├── ShareViewController.swift       # Share extension
│           └── ShareView.swift                # Share UI
├── macOS/
│   ├── MenuBarApp.swift                       # Menu bar app entry
│   ├── PopoverContentView.swift               # Popover content
│   ├── PreferencesWindow.swift                # Preferences window
│   ├── KeyboardShortcuts.swift                # Global shortcuts
│   └── AppleScriptSupport.swift               # Automation support
├── Shared/
│   ├── Models/
│   │   ├── Post.swift                         # Post data model
│   │   ├── PostStatus.swift                   # Status enumeration
│   │   ├── User.swift                         # User model
│   │   └── APIResponse.swift                  # API response models
│   ├── ViewModels/
│   │   ├── PostsViewModel.swift               # Main posts logic
│   │   ├── CreatePostViewModel.swift          # Post creation logic
│   │   ├── AuthViewModel.swift                # Authentication logic
│   │   └── SettingsViewModel.swift            # Settings management
│   ├── Services/
│   │   ├── APIService.swift                   # REST API client
│   │   ├── WebSocketService.swift             # Real-time updates
│   │   ├── NotificationService.swift          # Push notifications
│   │   ├── KeychainService.swift              # Secure storage
│   │   ├── CoreDataManager.swift              # Local persistence
│   │   └── NetworkMonitor.swift               # Network connectivity
│   ├── Components/
│   │   ├── PostCard.swift                     # Reusable post card
│   │   ├── LoadingView.swift                  # Loading indicator
│   │   ├── ErrorView.swift                    # Error display
│   │   ├── EmptyStateView.swift               # Empty state UI
│   │   └── SwipeActionsView.swift             # Custom swipe actions
│   └── Utilities/
│       ├── DateFormatters.swift               # Date formatting
│       ├── ImageCache.swift                   # Image caching
│       ├── HapticManager.swift                # Haptic feedback
│       └── Constants.swift                    # App constants
└── Resources/
    ├── LinkedInManager.xcdatamodeld           # Core Data model
    ├── Assets.xcassets                        # App assets
    └── Info.plist                             # App configuration
```

### 2.2 Core SwiftUI Views

#### PostListView (Main Dashboard)
```swift
import SwiftUI
import Combine

struct PostListView: View {
    @StateObject private var viewModel = PostsViewModel()
    @State private var selectedFilter = PostFilter.pending
    @State private var showCreatePost = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                PostFilterBar(selection: $selectedFilter)
                    .padding(.horizontal)
                
                if viewModel.isLoading && viewModel.posts.isEmpty {
                    LoadingView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if viewModel.posts.isEmpty {
                    EmptyStateView(
                        title: "No Posts",
                        message: "Create your first LinkedIn post to get started",
                        action: { showCreatePost = true }
                    )
                } else {
                    List(viewModel.filteredPosts) { post in
                        NavigationLink(destination: PostDetailView(post: post)) {
                            PostRowView(post: post)
                        }
                        .swipeActions(edge: .trailing) {
                            if post.status == .pending {
                                Button("Approve") {
                                    Task {
                                        await viewModel.approve(post)
                                    }
                                }
                                .tint(.green)
                                
                                Button("Reject") {
                                    Task {
                                        await viewModel.reject(post)
                                    }
                                }
                                .tint(.red)
                            }
                        }
                        .swipeActions(edge: .leading) {
                            if post.status == .published && post.linkedInURL != nil {
                                Button("View") {
                                    if let url = URL(string: post.linkedInURL!) {
                                        UIApplication.shared.open(url)
                                    }
                                }
                                .tint(.blue)
                            }
                        }
                    }
                    .refreshable {
                        await viewModel.refresh()
                    }
                }
            }
            .navigationTitle("LinkedIn Posts")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showCreatePost = true }) {
                        Image(systemName: "plus.circle.fill")
                            .font(.title2)
                    }
                }
                
                ToolbarItem(placement: .navigationBarLeading) {
                    Button(action: { viewModel.showSettings = true }) {
                        Image(systemName: "gearshape.fill")
                    }
                }
            }
        }
        .sheet(isPresented: $showCreatePost) {
            CreatePostView()
        }
        .sheet(isPresented: $viewModel.showSettings) {
            SettingsView()
        }
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK") { }
        } message: {
            Text(viewModel.errorMessage)
        }
        .task {
            await viewModel.loadPosts()
        }
        .onChange(of: selectedFilter) { filter in
            viewModel.filterPosts(by: filter)
        }
    }
}
```

#### PostDetailView
```swift
struct PostDetailView: View {
    let post: Post
    @StateObject private var viewModel = PostDetailViewModel()
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Post Header
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Post #\(post.id.prefix(8))")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Spacer()
                        
                        PostStatusBadge(status: post.status)
                    }
                    
                    Text(post.createdAt, style: .relative)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal)
                
                // LinkedIn Preview
                LinkedInPreviewView(post: post)
                    .padding(.horizontal)
                
                // Post Content
                VStack(alignment: .leading, spacing: 12) {
                    Text("Content")
                        .font(.headline)
                    
                    Text(post.content)
                        .font(.body)
                        .lineLimit(nil)
                }
                .padding(.horizontal)
                
                // Metadata
                if post.industry != nil || post.audience != nil {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Details")
                            .font(.headline)
                        
                        if let industry = post.industry {
                            Label(industry, systemImage: "building.2")
                        }
                        
                        if let audience = post.audience {
                            Label(audience, systemImage: "person.3")
                        }
                    }
                    .padding(.horizontal)
                }
                
                // Actions
                if post.status == .pending {
                    ApprovalActionsView(post: post, viewModel: viewModel)
                        .padding(.horizontal)
                }
                
                // Published Link
                if post.status == .published, let urlString = post.linkedInURL,
                   let url = URL(string: urlString) {
                    Link(destination: url) {
                        HStack {
                            Image(systemName: "link.circle.fill")
                            Text("View on LinkedIn")
                            Spacer()
                            Image(systemName: "arrow.up.right")
                        }
                        .padding()
                        .background(Color.blue.opacity(0.1))
                        .foregroundColor(.blue)
                        .cornerRadius(12)
                    }
                    .padding(.horizontal)
                }
            }
            .padding(.vertical)
        }
        .navigationTitle("Post Details")
        .navigationBarTitleDisplayMode(.inline)
        .alert("Confirmation", isPresented: $viewModel.showConfirmation) {
            Button("Cancel", role: .cancel) { }
            Button(viewModel.confirmationAction.title, role: viewModel.confirmationAction.isDestructive ? .destructive : .none) {
                Task {
                    await viewModel.executeConfirmedAction(post)
                }
            }
        } message: {
            Text(viewModel.confirmationMessage)
        }
    }
}
```

### 2.3 ViewModels Implementation

#### PostsViewModel
```swift
import Foundation
import Combine

@MainActor
class PostsViewModel: ObservableObject {
    @Published var posts: [Post] = []
    @Published var filteredPosts: [Post] = []
    @Published var isLoading = false
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var showSettings = false
    
    private var currentFilter: PostFilter = .pending
    private let apiService = APIService.shared
    private let webSocketService = WebSocketService.shared
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        setupWebSocketUpdates()
    }
    
    func loadPosts() async {
        isLoading = true
        
        do {
            let fetchedPosts = try await apiService.getPosts()
            posts = fetchedPosts
            filterPosts(by: currentFilter)
        } catch {
            handleError(error)
        }
        
        isLoading = false
    }
    
    func refresh() async {
        await loadPosts()
        HapticManager.shared.impactOccurred(.light)
    }
    
    func filterPosts(by filter: PostFilter) {
        currentFilter = filter
        
        filteredPosts = posts.filter { post in
            switch filter {
            case .all:
                return true
            case .pending:
                return post.status == .pending
            case .approved:
                return post.status == .approved
            case .published:
                return post.status == .published
            case .scheduled:
                return post.status == .scheduled
            }
        }
    }
    
    func approve(_ post: Post) async {
        do {
            try await apiService.approvePost(id: post.id)
            HapticManager.shared.notificationOccurred(.success)
            await loadPosts()
        } catch {
            handleError(error)
            HapticManager.shared.notificationOccurred(.error)
        }
    }
    
    func reject(_ post: Post) async {
        do {
            try await apiService.rejectPost(id: post.id, reason: "Rejected via swipe action")
            HapticManager.shared.notificationOccurred(.success)
            await loadPosts()
        } catch {
            handleError(error)
            HapticManager.shared.notificationOccurred(.error)
        }
    }
    
    private func setupWebSocketUpdates() {
        webSocketService.messagePublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] message in
                self?.handleWebSocketMessage(message)
            }
            .store(in: &cancellables)
    }
    
    private func handleWebSocketMessage(_ message: WebSocketMessage) {
        switch message.type {
        case .postUpdated:
            if let updatedPost = message.post {
                updatePost(updatedPost)
            }
        case .postCreated:
            if let newPost = message.post {
                posts.insert(newPost, at: 0)
                filterPosts(by: currentFilter)
            }
        case .postDeleted:
            if let postId = message.postId {
                posts.removeAll { $0.id == postId }
                filterPosts(by: currentFilter)
            }
        }
    }
    
    private func updatePost(_ updatedPost: Post) {
        if let index = posts.firstIndex(where: { $0.id == updatedPost.id }) {
            posts[index] = updatedPost
            filterPosts(by: currentFilter)
        }
    }
    
    private func handleError(_ error: Error) {
        errorMessage = error.localizedDescription
        showError = true
    }
}
```

---

## 3. System Integration

### 3.1 API Service Implementation

```swift
import Foundation
import Network

class APIService: ObservableObject {
    static let shared = APIService()
    
    private let baseURL = "http://localhost:8000/api"
    private let session = URLSession.shared
    private let keychain = KeychainService.shared
    
    private init() {}
    
    // MARK: - Authentication
    
    func authenticate(deviceId: String) async throws -> AuthResponse {
        let request = try createRequest(
            endpoint: "/auth/login",
            method: "POST",
            body: ["device_id": deviceId]
        )
        
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        
        let authResponse = try JSONDecoder().decode(AuthResponse.self, from: data)
        
        // Store tokens securely
        try keychain.store(authResponse.accessToken, for: .accessToken)
        try keychain.store(authResponse.refreshToken, for: .refreshToken)
        
        return authResponse
    }
    
    // MARK: - Posts
    
    func getPosts(page: Int = 1, limit: Int = 50) async throws -> [Post] {
        let request = try createAuthenticatedRequest(
            endpoint: "/posts?page=\(page)&limit=\(limit)",
            method: "GET"
        )
        
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        
        let postsResponse = try JSONDecoder().decode(PostsResponse.self, from: data)
        return postsResponse.posts
    }
    
    func createPost(_ post: CreatePostRequest) async throws -> Post {
        let request = try createAuthenticatedRequest(
            endpoint: "/posts",
            method: "POST",
            body: post
        )
        
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        
        return try JSONDecoder().decode(Post.self, from: data)
    }
    
    func approvePost(id: String) async throws {
        let request = try createAuthenticatedRequest(
            endpoint: "/approvals/\(id)/approve",
            method: "POST"
        )
        
        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }
    
    func rejectPost(id: String, reason: String) async throws {
        let request = try createAuthenticatedRequest(
            endpoint: "/approvals/\(id)/reject",
            method: "POST",
            body: ["reason": reason]
        )
        
        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }
    
    // MARK: - Publishing
    
    func publishPost(id: String) async throws {
        let request = try createAuthenticatedRequest(
            endpoint: "/publish/\(id)",
            method: "POST"
        )
        
        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }
    
    // MARK: - Utilities
    
    func generateMockup(for postId: String) async throws -> Data {
        let request = try createAuthenticatedRequest(
            endpoint: "/mockup/\(postId)",
            method: "GET"
        )
        
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        
        return data
    }
    
    // MARK: - Private Helpers
    
    private func createRequest(endpoint: String, method: String, body: Any? = nil) throws -> URLRequest {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let body = body {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        
        return request
    }
    
    private func createAuthenticatedRequest(endpoint: String, method: String, body: Any? = nil) throws -> URLRequest {
        var request = try createRequest(endpoint: endpoint, method: method, body: body)
        
        guard let token = try keychain.retrieve(.accessToken) else {
            throw APIError.noAccessToken
        }
        
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        return request
    }
    
    private func validateResponse(_ response: URLResponse) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard 200...299 ~= httpResponse.statusCode else {
            switch httpResponse.statusCode {
            case 401:
                throw APIError.unauthorized
            case 403:
                throw APIError.forbidden
            case 404:
                throw APIError.notFound
            case 500...599:
                throw APIError.serverError
            default:
                throw APIError.unknownError(httpResponse.statusCode)
            }
        }
    }
}
```

### 3.2 WebSocket Service

```swift
import Foundation
import Combine

class WebSocketService: ObservableObject {
    static let shared = WebSocketService()
    
    private var webSocketTask: URLSessionWebSocketTask?
    private let messageSubject = PassthroughSubject<WebSocketMessage, Never>()
    
    var messagePublisher: AnyPublisher<WebSocketMessage, Never> {
        messageSubject.eraseToAnyPublisher()
    }
    
    private init() {}
    
    func connect() {
        guard let url = URL(string: "ws://localhost:8000/ws/updates") else { return }
        
        webSocketTask = URLSession.shared.webSocketTask(with: url)
        webSocketTask?.resume()
        
        listen()
    }
    
    func disconnect() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
    }
    
    private func listen() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                self?.handleMessage(message)
                self?.listen() // Continue listening
            case .failure(let error):
                print("WebSocket error: \(error)")
                // Implement reconnection logic here
                DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                    self?.connect()
                }
            }
        }
    }
    
    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            if let data = text.data(using: .utf8),
               let webSocketMessage = try? JSONDecoder().decode(WebSocketMessage.self, from: data) {
                messageSubject.send(webSocketMessage)
            }
        case .data(let data):
            if let webSocketMessage = try? JSONDecoder().decode(WebSocketMessage.self, from: data) {
                messageSubject.send(webSocketMessage)
            }
        @unknown default:
            break
        }
    }
}
```

### 3.3 Core Data Integration

```swift
import CoreData
import CloudKit

class CoreDataManager: ObservableObject {
    static let shared = CoreDataManager()
    
    lazy var persistentContainer: NSPersistentCloudKitContainer = {
        let container = NSPersistentCloudKitContainer(name: "LinkedInManager")
        
        // Configure for CloudKit
        container.persistentStoreDescriptions.forEach { description in
            description.setOption(true as NSNumber, forKey: NSPersistentHistoryTrackingKey)
            description.setOption(true as NSNumber, forKey: NSPersistentStoreRemoteChangeNotificationPostOptionKey)
            description.configuration = "CloudConfiguration"
        }
        
        container.loadPersistentStores { _, error in
            if let error = error {
                fatalError("Core Data error: \(error.localizedDescription)")
            }
        }
        
        container.viewContext.automaticallyMergesChangesFromParent = true
        
        return container
    }()
    
    var context: NSManagedObjectContext {
        persistentContainer.viewContext
    }
    
    func save() {
        if context.hasChanges {
            try? context.save()
        }
    }
    
    // MARK: - Post Operations
    
    func createPost(from apiPost: Post) -> PostEntity {
        let entity = PostEntity(context: context)
        entity.id = apiPost.id
        entity.content = apiPost.content
        entity.status = apiPost.status.rawValue
        entity.createdAt = apiPost.createdAt
        entity.updatedAt = apiPost.updatedAt
        entity.industry = apiPost.industry
        entity.audience = apiPost.audience
        entity.goldenThreads = apiPost.goldenThreads
        entity.imageURL = apiPost.imageURL
        entity.linkedInURL = apiPost.linkedInURL
        entity.lastSynced = Date()
        
        save()
        return entity
    }
    
    func updatePost(_ entity: PostEntity, from apiPost: Post) {
        entity.content = apiPost.content
        entity.status = apiPost.status.rawValue
        entity.updatedAt = apiPost.updatedAt
        entity.approvedAt = apiPost.approvedAt
        entity.publishedAt = apiPost.publishedAt
        entity.industry = apiPost.industry
        entity.audience = apiPost.audience
        entity.goldenThreads = apiPost.goldenThreads
        entity.imageURL = apiPost.imageURL
        entity.linkedInURL = apiPost.linkedInURL
        entity.lastSynced = Date()
        
        save()
    }
    
    func fetchPosts() -> [PostEntity] {
        let request: NSFetchRequest<PostEntity> = PostEntity.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(keyPath: \PostEntity.createdAt, ascending: false)]
        
        do {
            return try context.fetch(request)
        } catch {
            print("Failed to fetch posts: \(error)")
            return []
        }
    }
    
    func deletePost(_ entity: PostEntity) {
        context.delete(entity)
        save()
    }
}
```

---

## 4. Platform-Specific Features

### 4.1 iOS Features

#### Widget Implementation
```swift
import WidgetKit
import SwiftUI

struct PendingPostsWidget: Widget {
    let kind: String = "PendingPostsWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: PendingPostsProvider()) { entry in
            PendingPostsWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("Pending Posts")
        .description("View posts awaiting approval")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
        .contentMarginsDisabled()
    }
}

struct PendingPostsEntry: TimelineEntry {
    let date: Date
    let pendingPosts: [Post]
    let isPlaceholder: Bool
}

struct PendingPostsProvider: TimelineProvider {
    func placeholder(in context: Context) -> PendingPostsEntry {
        PendingPostsEntry(
            date: Date(),
            pendingPosts: Post.mockPendingPosts,
            isPlaceholder: true
        )
    }
    
    func getSnapshot(in context: Context, completion: @escaping (PendingPostsEntry) -> ()) {
        let entry = PendingPostsEntry(
            date: Date(),
            pendingPosts: Post.mockPendingPosts,
            isPlaceholder: context.isPreview
        )
        completion(entry)
    }
    
    func getTimeline(in context: Context, completion: @escaping (Timeline<PendingPostsEntry>) -> ()) {
        Task {
            do {
                let posts = try await APIService.shared.getPendingPosts()
                let entry = PendingPostsEntry(
                    date: Date(),
                    pendingPosts: Array(posts.prefix(5)),
                    isPlaceholder: false
                )
                
                let timeline = Timeline(
                    entries: [entry],
                    policy: .after(Calendar.current.date(byAdding: .minute, value: 15, to: Date()) ?? Date())
                )
                completion(timeline)
            } catch {
                let entry = PendingPostsEntry(
                    date: Date(),
                    pendingPosts: [],
                    isPlaceholder: false
                )
                let timeline = Timeline(entries: [entry], policy: .after(Date().addingTimeInterval(900)))
                completion(timeline)
            }
        }
    }
}

struct PendingPostsWidgetEntryView: View {
    var entry: PendingPostsProvider.Entry
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "newspaper.fill")
                    .foregroundColor(.blue)
                Text("Pending Posts")
                    .font(.headline)
                Spacer()
                Text("\(entry.pendingPosts.count)")
                    .font(.title2)
                    .bold()
                    .foregroundColor(.blue)
            }
            
            if entry.pendingPosts.isEmpty {
                Text("No pending posts")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Spacer()
            } else {
                ForEach(entry.pendingPosts.prefix(3), id: \.id) { post in
                    VStack(alignment: .leading, spacing: 2) {
                        Text(post.content)
                            .font(.caption)
                            .lineLimit(2)
                        
                        Text(post.createdAt, style: .relative)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    
                    if post != entry.pendingPosts.prefix(3).last {
                        Divider()
                    }
                }
                
                if entry.pendingPosts.count > 3 {
                    Text("and \(entry.pendingPosts.count - 3) more...")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
            }
        }
        .padding()
        .widgetURL(URL(string: "linkedinmanager://posts/pending"))
    }
}
```

#### Share Extension
```swift
import UIKit
import Social
import UniformTypeIdentifiers

class ShareViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        setupUI()
        processSharedContent()
    }
    
    private func setupUI() {
        view.backgroundColor = .systemBackground
        
        let hostView = UIHostingController(rootView: ShareView(
            onCancel: { [weak self] in
                self?.extensionContext?.cancelRequest(withError: NSError(domain: "UserCancelled", code: 0))
            },
            onSubmit: { [weak self] content in
                self?.submitPost(content: content)
            }
        ))
        
        addChild(hostView)
        view.addSubview(hostView.view)
        hostView.view.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            hostView.view.topAnchor.constraint(equalTo: view.topAnchor),
            hostView.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            hostView.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            hostView.view.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
        hostView.didMove(toParent: self)
    }
    
    private func processSharedContent() {
        guard let extensionItem = extensionContext?.inputItems.first as? NSExtensionItem,
              let attachments = extensionItem.attachments else { return }
        
        for attachment in attachments {
            if attachment.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) {
                attachment.loadItem(forTypeIdentifier: UTType.plainText.identifier) { [weak self] data, error in
                    DispatchQueue.main.async {
                        if let text = data as? String {
                            self?.handleSharedText(text)
                        }
                    }
                }
            } else if attachment.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                attachment.loadItem(forTypeIdentifier: UTType.url.identifier) { [weak self] data, error in
                    DispatchQueue.main.async {
                        if let url = data as? URL {
                            self?.handleSharedURL(url)
                        }
                    }
                }
            }
        }
    }
    
    private func handleSharedText(_ text: String) {
        // Process shared text - could be article content, thoughts, etc.
        // Show in the share UI for user to modify
    }
    
    private func handleSharedURL(_ url: URL) {
        // Process shared URL - could be article link, company page, etc.
        // Extract content or use as reference
    }
    
    private func submitPost(content: String) {
        Task {
            do {
                let createRequest = CreatePostRequest(
                    content: content,
                    industry: nil,
                    audience: nil,
                    goldenThreads: nil,
                    imageURL: nil,
                    scheduledFor: nil
                )
                
                _ = try await APIService.shared.createPost(createRequest)
                
                DispatchQueue.main.async {
                    self.extensionContext?.completeRequest(returningItems: nil)
                }
            } catch {
                DispatchQueue.main.async {
                    self.extensionContext?.cancelRequest(withError: error)
                }
            }
        }
    }
}
```

#### Shortcuts Integration
```swift
import Intents
import IntentsUI

class IntentHandler: INExtension {
    override func handler(for intent: INIntent) -> Any? {
        if intent is CreatePostIntent {
            return CreatePostIntentHandler()
        } else if intent is ApprovePostIntent {
            return ApprovePostIntentHandler()
        }
        return nil
    }
}

class CreatePostIntentHandler: NSObject, CreatePostIntentHandling {
    func handle(intent: CreatePostIntent, completion: @escaping (CreatePostIntentResponse) -> Void) {
        guard let content = intent.content, !content.isEmpty else {
            completion(CreatePostIntentResponse(code: .failure, userActivity: nil))
            return
        }
        
        Task {
            do {
                let createRequest = CreatePostRequest(
                    content: content,
                    industry: intent.industry,
                    audience: intent.audience,
                    goldenThreads: intent.goldenThreads,
                    imageURL: nil,
                    scheduledFor: nil
                )
                
                let post = try await APIService.shared.createPost(createRequest)
                
                let response = CreatePostIntentResponse(code: .success, userActivity: nil)
                response.postId = post.id
                completion(response)
            } catch {
                completion(CreatePostIntentResponse(code: .failure, userActivity: nil))
            }
        }
    }
    
    func resolveContent(for intent: CreatePostIntent, with completion: @escaping (INStringResolutionResult) -> Void) {
        if let content = intent.content, !content.isEmpty {
            completion(INStringResolutionResult.success(with: content))
        } else {
            completion(INStringResolutionResult.needsValue())
        }
    }
}
```

### 4.2 macOS Features

#### Menu Bar App
```swift
import SwiftUI
import AppKit

@main
struct MenuBarApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    var body: some Scene {
        Settings {
            PreferencesView()
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private var popover = NSPopover()
    private var statusBarButton: NSStatusBarButton?
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        setupStatusBar()
        setupPopover()
        setupGlobalShortcuts()
    }
    
    private func setupStatusBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        
        if let button = statusItem.button {
            button.image = NSImage(systemSymbolName: "newspaper.fill", accessibilityDescription: "LinkedIn Manager")
            button.image?.isTemplate = true
            button.action = #selector(togglePopover)
            button.target = self
            statusBarButton = button
        }
        
        updateStatusBarBadge()
    }
    
    private func setupPopover() {
        popover.contentSize = NSSize(width: 360, height: 480)
        popover.behavior = .transient
        popover.contentViewController = NSHostingController(rootView: PopoverContentView())
    }
    
    private func setupGlobalShortcuts() {
        // Register global shortcut: Cmd+Shift+L
        NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { event in
            if event.modifierFlags.contains([.command, .shift]) && event.keyCode == 37 { // L key
                self.togglePopover()
            }
        }
    }
    
    @objc private func togglePopover() {
        if popover.isShown {
            popover.performClose(nil)
        } else {
            showPopover()
        }
    }
    
    private func showPopover() {
        if let button = statusBarButton {
            popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
        }
    }
    
    private func updateStatusBarBadge() {
        Task {
            do {
                let pendingPosts = try await APIService.shared.getPendingPosts()
                DispatchQueue.main.async {
                    if pendingPosts.count > 0 {
                        self.statusBarButton?.image = NSImage(systemSymbolName: "newspaper.fill", accessibilityDescription: "\(pendingPosts.count) pending posts")
                        NSApp.dockTile.badgeLabel = "\(pendingPosts.count)"
                    } else {
                        self.statusBarButton?.image = NSImage(systemSymbolName: "newspaper", accessibilityDescription: "No pending posts")
                        NSApp.dockTile.badgeLabel = nil
                    }
                }
            } catch {
                print("Failed to update status bar badge: \(error)")
            }
        }
    }
}
```

#### AppleScript Support
```swift
import ScriptingBridge

@objc(LinkedInManagerApplication)
class LinkedInManagerApplication: NSApplication {
    
    @objc func createPost(withContent content: String) -> String? {
        let createRequest = CreatePostRequest(
            content: content,
            industry: nil,
            audience: nil,
            goldenThreads: nil,
            imageURL: nil,
            scheduledFor: nil
        )
        
        // This would need to be made synchronous for AppleScript
        // In practice, you'd want to use a completion-based approach
        return "post-id-placeholder"
    }
    
    @objc func approvePosts() -> Int32 {
        // Approve all pending posts
        // Return count of approved posts
        return 0
    }
    
    @objc var pendingPostsCount: Int32 {
        // Return current count of pending posts
        return 0
    }
}

// AppleScript usage example:
/*
tell application "LinkedIn Manager"
    set newPostId to create post with content "This is a test post from AppleScript"
    set pendingCount to pending posts count
    approve posts
end tell
*/
```

---

## 5. Implementation Phases

### Phase 1: Backend API Development (Weeks 1-4)

#### Week 1: Core Infrastructure
- [ ] Setup FastAPI project structure
- [ ] Database connection and models
- [ ] JWT authentication system
- [ ] Basic CRUD endpoints for posts
- [ ] Health check and monitoring endpoints

#### Week 2: Approval Workflow
- [ ] Approval/rejection endpoints
- [ ] Status tracking system
- [ ] WebSocket real-time updates
- [ ] Rate limiting and validation

#### Week 3: LinkedIn Integration
- [ ] LinkedIn API wrapper
- [ ] Publishing functionality
- [ ] Scheduled posts system
- [ ] Error handling and retry logic

#### Week 4: Utilities and Testing
- [ ] Mockup generation API
- [ ] Push notification service
- [ ] API documentation
- [ ] Integration testing

### Phase 2: iOS Core Application (Weeks 5-8)

#### Week 5: Project Foundation
- [ ] Xcode project setup (iOS/macOS targets)
- [ ] Core Data model design
- [ ] API service implementation
- [ ] Authentication flow
- [ ] Basic navigation structure

#### Week 6: Post Management
- [ ] Post list view implementation
- [ ] Post detail view
- [ ] Pull-to-refresh functionality
- [ ] Search and filtering
- [ ] Basic error handling

#### Week 7: Approval Workflow
- [ ] Swipe actions for approval/rejection
- [ ] Approval buttons and confirmations
- [ ] LinkedIn preview generation
- [ ] Status tracking and updates
- [ ] Haptic feedback integration

#### Week 8: Post Creation
- [ ] Create post form
- [ ] Industry and audience selection
- [ ] Golden threads integration
- [ ] Character counting and validation
- [ ] Image attachment support

### Phase 3: iOS Extensions (Weeks 9-10)

#### Week 9: Home Screen Widget
- [ ] Widget extension setup
- [ ] Pending posts widget implementation
- [ ] Timeline provider
- [ ] Widget configuration
- [ ] Deep linking integration

#### Week 10: Share Extension & Shortcuts
- [ ] Share extension for content creation
- [ ] Shortcuts app integration
- [ ] Intent definitions
- [ ] Voice command support
- [ ] Background processing

### Phase 3: macOS Application (Weeks 11-12)

#### Week 11: Menu Bar App
- [ ] macOS target setup
- [ ] Menu bar integration
- [ ] Popover interface
- [ ] Global keyboard shortcuts
- [ ] System notifications

#### Week 12: macOS Features
- [ ] Preferences window
- [ ] AppleScript support
- [ ] Touch Bar integration (if applicable)
- [ ] Dock badge notifications
- [ ] Window management

### Phase 4: Polish & Integration (Weeks 13-14)

#### Week 13: UI Polish
- [ ] Design system consistency
- [ ] Accessibility improvements
- [ ] Dark mode support
- [ ] iPad-specific layouts
- [ ] Animation and transitions

#### Week 14: Testing & Bug Fixes
- [ ] Unit test coverage
- [ ] UI test automation
- [ ] Integration testing
- [ ] Performance optimization
- [ ] Beta testing feedback

### Phase 5: Deployment (Weeks 15-16)

#### Week 15: Production Preparation
- [ ] Backend containerization
- [ ] Kubernetes deployment
- [ ] SSL certificates and domain setup
- [ ] App Store metadata and screenshots
- [ ] Privacy policy and terms of service

#### Week 16: Release & Monitoring
- [ ] App Store submission
- [ ] Production deployment
- [ ] Monitoring and alerting setup
- [ ] User onboarding flow
- [ ] Post-launch support

---

## 6. Security Implementation

### 6.1 API Security

#### JWT Token Management
```python
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

class SecurityManager:
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 30
    
    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                raise JWTError("Invalid token type")
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

#### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/posts")
@limiter.limit("10/minute")
async def create_post(request: Request, post: CreatePostRequest):
    # Post creation logic
    pass

@app.post("/api/approvals/{post_id}/approve")
@limiter.limit("30/minute")
async def approve_post(request: Request, post_id: str):
    # Approval logic
    pass
```

### 6.2 iOS Security

#### Keychain Service
```swift
import Security
import Foundation

enum KeychainKey: String, CaseIterable {
    case accessToken = "access_token"
    case refreshToken = "refresh_token"
    case deviceId = "device_id"
    case apiKey = "api_key"
}

class KeychainService {
    static let shared = KeychainService()
    
    private init() {}
    
    func store(_ value: String, for key: KeychainKey) throws {
        let data = value.data(using: .utf8)!
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key.rawValue,
            kSecAttrService as String: Bundle.main.bundleIdentifier!,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        
        // Delete existing item
        SecItemDelete(query as CFDictionary)
        
        // Add new item
        let status = SecItemAdd(query as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw KeychainError.unableToStore(status)
        }
    }
    
    func retrieve(_ key: KeychainKey) throws -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key.rawValue,
            kSecAttrService as String: Bundle.main.bundleIdentifier!,
            kSecReturnData as String: kCFBooleanTrue!,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        switch status {
        case errSecSuccess:
            guard let data = result as? Data,
                  let string = String(data: data, encoding: .utf8) else {
                throw KeychainError.unexpectedData
            }
            return string
        case errSecItemNotFound:
            return nil
        default:
            throw KeychainError.unableToRetrieve(status)
        }
    }
    
    func delete(_ key: KeychainKey) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key.rawValue,
            kSecAttrService as String: Bundle.main.bundleIdentifier!
        ]
        
        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw KeychainError.unableToDelete(status)
        }
    }
    
    func deleteAll() throws {
        for key in KeychainKey.allCases {
            try delete(key)
        }
    }
}

enum KeychainError: Error, LocalizedError {
    case unableToStore(OSStatus)
    case unableToRetrieve(OSStatus)
    case unableToDelete(OSStatus)
    case unexpectedData
    
    var errorDescription: String? {
        switch self {
        case .unableToStore(let status):
            return "Unable to store item in keychain. Status: \(status)"
        case .unableToRetrieve(let status):
            return "Unable to retrieve item from keychain. Status: \(status)"
        case .unableToDelete(let status):
            return "Unable to delete item from keychain. Status: \(status)"
        case .unexpectedData:
            return "Unexpected data found in keychain"
        }
    }
}
```

#### Biometric Authentication
```swift
import LocalAuthentication

class BiometricAuthManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var authenticationError: String?
    
    func authenticateUser() {
        let context = LAContext()
        var error: NSError?
        
        // Check if biometric authentication is available
        if context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) {
            let reason = "Authenticate to access LinkedIn Manager"
            
            context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: reason) { success, authenticationError in
                DispatchQueue.main.async {
                    if success {
                        self.isAuthenticated = true
                        self.authenticationError = nil
                    } else {
                        self.isAuthenticated = false
                        self.authenticationError = authenticationError?.localizedDescription
                    }
                }
            }
        } else {
            // Fallback to device passcode
            if context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error) {
                let reason = "Authenticate to access LinkedIn Manager"
                
                context.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: reason) { success, authenticationError in
                    DispatchQueue.main.async {
                        if success {
                            self.isAuthenticated = true
                            self.authenticationError = nil
                        } else {
                            self.isAuthenticated = false
                            self.authenticationError = authenticationError?.localizedDescription
                        }
                    }
                }
            } else {
                DispatchQueue.main.async {
                    self.authenticationError = "No authentication method available"
                }
            }
        }
    }
}
```

#### Certificate Pinning
```swift
import Foundation
import Network

class CertificatePinner: NSObject, URLSessionDelegate {
    private let pinnedCertificates: Set<Data>
    
    init(certificates: [String]) {
        self.pinnedCertificates = Set(certificates.compactMap { certName in
            guard let path = Bundle.main.path(forResource: certName, ofType: "cer"),
                  let data = NSData(contentsOfFile: path) as Data? else {
                return nil
            }
            return data
        })
        super.init()
    }
    
    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        
        // Get the server trust
        guard let serverTrust = challenge.protectionSpace.serverTrust else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Evaluate the server trust
        var result: SecTrustResultType = .invalid
        let status = SecTrustEvaluate(serverTrust, &result)
        
        guard status == errSecSuccess else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Get the server certificate
        guard let serverCertificate = SecTrustGetCertificateAtIndex(serverTrust, 0) else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Get the certificate data
        let serverCertificateData = SecCertificateCopyData(serverCertificate)
        let data = CFDataGetBytePtr(serverCertificateData)
        let size = CFDataGetLength(serverCertificateData)
        let certificateData = NSData(bytes: data, length: size) as Data
        
        // Check if the certificate matches our pinned certificates
        if pinnedCertificates.contains(certificateData) {
            completionHandler(.useCredential, URLCredential(trust: serverTrust))
        } else {
            completionHandler(.cancelAuthenticationChallenge, nil)
        }
    }
}
```

---

## 7. Performance Optimization

### 7.1 Backend Performance

#### Database Connection Pooling
```python
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine

# Configure connection pool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)
```

#### Caching Strategy
```python
import redis
from functools import wraps
import json
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result, default=str))
            
            return result
        return wrapper
    return decorator

@cache_result(expiration=60)
async def get_posts_cached(page: int, limit: int):
    return await get_posts(page, limit)
```

### 7.2 iOS Performance

#### Image Caching
```swift
import Foundation
import UIKit

class ImageCache {
    static let shared = ImageCache()
    
    private let memoryCache = NSCache<NSString, UIImage>()
    private let fileManager = FileManager.default
    private let cacheDirectory: URL
    
    private init() {
        // Configure memory cache
        memoryCache.countLimit = 100
        memoryCache.totalCostLimit = 100 * 1024 * 1024 // 100MB
        
        // Setup disk cache directory
        cacheDirectory = fileManager.urls(for: .cachesDirectory, in: .userDomainMask)
            .first!.appendingPathComponent("ImageCache")
        
        try? fileManager.createDirectory(at: cacheDirectory, withIntermediateDirectories: true)
        
        // Clean old cache files on startup
        cleanExpiredCache()
    }
    
    func image(for url: URL) -> UIImage? {
        let key = cacheKey(for: url)
        
        // Check memory cache first
        if let cachedImage = memoryCache.object(forKey: key) {
            return cachedImage
        }
        
        // Check disk cache
        let fileURL = cacheDirectory.appendingPathComponent(key.components(separatedBy: "/").joined(separator: "_"))
        if let imageData = try? Data(contentsOf: fileURL),
           let image = UIImage(data: imageData) {
            // Store in memory cache
            memoryCache.setObject(image, forKey: key)
            return image
        }
        
        return nil
    }
    
    func setImage(_ image: UIImage, for url: URL) {
        let key = cacheKey(for: url)
        
        // Store in memory cache
        memoryCache.setObject(image, forKey: key)
        
        // Store in disk cache
        let fileURL = cacheDirectory.appendingPathComponent(key.components(separatedBy: "/").joined(separator: "_"))
        
        DispatchQueue.global(qos: .background).async {
            if let data = image.pngData() {
                try? data.write(to: fileURL)
            }
        }
    }
    
    func loadImage(from url: URL) async throws -> UIImage {
        // Check cache first
        if let cachedImage = image(for: url) {
            return cachedImage
        }
        
        // Download image
        let (data, _) = try await URLSession.shared.data(from: url)
        guard let image = UIImage(data: data) else {
            throw ImageCacheError.invalidImageData
        }
        
        // Cache the image
        setImage(image, for: url)
        
        return image
    }
    
    private func cacheKey(for url: URL) -> NSString {
        return url.absoluteString as NSString
    }
    
    private func cleanExpiredCache() {
        let expirationDate = Date().addingTimeInterval(-7 * 24 * 60 * 60) // 7 days ago
        
        DispatchQueue.global(qos: .utility).async {
            guard let fileURLs = try? self.fileManager.contentsOfDirectory(at: self.cacheDirectory, includingPropertiesForKeys: [.creationDateKey]) else { return }
            
            for fileURL in fileURLs {
                guard let creationDate = try? fileURL.resourceValues(forKeys: [.creationDateKey]).creationDate else { continue }
                
                if creationDate < expirationDate {
                    try? self.fileManager.removeItem(at: fileURL)
                }
            }
        }
    }
}

enum ImageCacheError: Error {
    case invalidImageData
}
```

#### Background App Refresh
```swift
import BackgroundTasks

class BackgroundTaskManager {
    static let shared = BackgroundTaskManager()
    
    private let refreshIdentifier = "com.linkedinmanager.refresh"
    private let processingIdentifier = "com.linkedinmanager.processing"
    
    func registerBackgroundTasks() {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: refreshIdentifier, using: nil) { task in
            self.handleAppRefresh(task: task as! BGAppRefreshTask)
        }
        
        BGTaskScheduler.shared.register(forTaskWithIdentifier: processingIdentifier, using: nil) { task in
            self.handleProcessing(task: task as! BGProcessingTask)
        }
    }
    
    func scheduleAppRefresh() {
        let request = BGAppRefreshTaskRequest(identifier: refreshIdentifier)
        request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60) // 15 minutes
        
        do {
            try BGTaskScheduler.shared.submit(request)
            print("Background refresh scheduled")
        } catch {
            print("Could not schedule app refresh: \(error)")
        }
    }
    
    func scheduleProcessing() {
        let request = BGProcessingTaskRequest(identifier: processingIdentifier)
        request.earliestBeginDate = Date(timeIntervalSinceNow: 5 * 60) // 5 minutes
        request.requiresNetworkConnectivity = true
        
        do {
            try BGTaskScheduler.shared.submit(request)
            print("Background processing scheduled")
        } catch {
            print("Could not schedule processing: \(error)")
        }
    }
    
    private func handleAppRefresh(task: BGAppRefreshTask) {
        scheduleAppRefresh() // Schedule next refresh
        
        let operation = BlockOperation {
            // Sync posts with server
            Task {
                do {
                    let posts = try await APIService.shared.getPosts()
                    await CoreDataManager.shared.syncPosts(posts)
                    task.setTaskCompleted(success: true)
                } catch {
                    task.setTaskCompleted(success: false)
                }
            }
        }
        
        task.expirationHandler = {
            operation.cancel()
            task.setTaskCompleted(success: false)
        }
        
        let operationQueue = OperationQueue()
        operationQueue.addOperation(operation)
    }
    
    private func handleProcessing(task: BGProcessingTask) {
        scheduleProcessing() // Schedule next processing
        
        let operation = BlockOperation {
            // Process pending approvals, publish scheduled posts, etc.
            Task {
                do {
                    // Sync and process data
                    await self.processScheduledPosts()
                    await self.cleanupOldData()
                    task.setTaskCompleted(success: true)
                } catch {
                    task.setTaskCompleted(success: false)
                }
            }
        }
        
        task.expirationHandler = {
            operation.cancel()
            task.setTaskCompleted(success: false)
        }
        
        let operationQueue = OperationQueue()
        operationQueue.addOperation(operation)
    }
    
    private func processScheduledPosts() async {
        // Implementation for processing scheduled posts
    }
    
    private func cleanupOldData() async {
        // Implementation for cleaning up old cached data
    }
}
```

---

## 8. Deployment Strategy

### 8.1 Backend Deployment

#### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Kubernetes Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: linkedin-manager-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: linkedin-manager-api
  template:
    metadata:
      labels:
        app: linkedin-manager-api
    spec:
      containers:
      - name: api
        image: linkedin-manager-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: linkedin-secrets
              key: database-url
        - name: LINKEDIN_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: linkedin-secrets
              key: linkedin-client-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: linkedin-manager-service
spec:
  selector:
    app: linkedin-manager-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: linkedin-manager-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.linkedinmanager.com
    secretName: linkedin-manager-tls
  rules:
  - host: api.linkedinmanager.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: linkedin-manager-service
            port:
              number: 80
```

### 8.2 iOS App Store Deployment

#### App Store Connect Configuration
```swift
// Info.plist configuration
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>LinkedIn Manager</string>
    <key>CFBundleIdentifier</key>
    <string>com.yourcompany.linkedinmanager</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    
    <!-- URL Schemes -->
    <key>CFBundleURLTypes</key>
    <array>
        <dict>
            <key>CFBundleURLName</key>
            <string>com.yourcompany.linkedinmanager</string>
            <key>CFBundleURLSchemes</key>
            <array>
                <string>linkedinmanager</string>
            </array>
        </dict>
    </array>
    
    <!-- Background Modes -->
    <key>UIBackgroundModes</key>
    <array>
        <string>background-app-refresh</string>
        <string>background-processing</string>
        <string>remote-notification</string>
    </array>
    
    <!-- Background Task Identifiers -->
    <key>BGTaskSchedulerPermittedIdentifiers</key>
    <array>
        <string>com.linkedinmanager.refresh</string>
        <string>com.linkedinmanager.processing</string>
    </array>
    
    <!-- Privacy Descriptions -->
    <key>NSFaceIDUsageDescription</key>
    <string>Use Face ID to securely access your LinkedIn post manager</string>
    <key>NSCameraUsageDescription</key>
    <string>Take photos to include with your LinkedIn posts</string>
    <key>NSPhotoLibraryUsageDescription</key>
    <string>Select photos from your library to include with posts</string>
    
    <!-- Network Security -->
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <false/>
        <key>NSExceptionDomains</key>
        <dict>
            <key>api.linkedinmanager.com</key>
            <dict>
                <key>NSExceptionRequiresForwardSecrecy</key>
                <false/>
                <key>NSExceptionMinimumTLSVersion</key>
                <string>TLSv1.2</string>
            </dict>
        </dict>
    </dict>
</dict>
</plist>
```

#### Build and Archive Script
```bash
#!/bin/bash
# build_and_archive.sh

set -e

# Configuration
SCHEME="LinkedIn Manager"
WORKSPACE="LinkedInManager.xcworkspace"
ARCHIVE_PATH="./build/LinkedInManager.xcarchive"
EXPORT_PATH="./build/export"

# Clean previous builds
rm -rf ./build

# Create build directory
mkdir -p ./build

# Archive iOS app
echo "Archiving iOS app..."
xcodebuild archive \
    -workspace "$WORKSPACE" \
    -scheme "$SCHEME" \
    -configuration Release \
    -destination "generic/platform=iOS" \
    -archivePath "$ARCHIVE_PATH" \
    -allowProvisioningUpdates

# Export for App Store
echo "Exporting for App Store..."
xcodebuild -exportArchive \
    -archivePath "$ARCHIVE_PATH" \
    -exportPath "$EXPORT_PATH" \
    -exportOptionsPlist ./ExportOptions.plist

# Upload to App Store Connect (optional)
# xcrun altool --upload-app --file "$EXPORT_PATH/LinkedIn Manager.ipa" --username "$APPLE_ID" --password "$APP_SPECIFIC_PASSWORD"

echo "Build and export completed successfully!"
echo "IPA location: $EXPORT_PATH/"
```

---

## 9. Monitoring and Analytics

### 9.1 Backend Monitoring
```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request
import time

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 9.2 iOS Analytics
```swift
import os.log

class AnalyticsManager {
    static let shared = AnalyticsManager()
    
    private let logger = Logger(subsystem: Bundle.main.bundleIdentifier!, category: "Analytics")
    
    func trackEvent(_ event: AnalyticsEvent, parameters: [String: Any] = [:]) {
        logger.info("Analytics: \(event.rawValue) - \(parameters)")
        
        // Send to your analytics service
        Task {
            await sendEvent(event, parameters: parameters)
        }
    }
    
    func trackPostAction(_ action: PostAction, postId: String) {
        trackEvent(.postAction, parameters: [
            "action": action.rawValue,
            "post_id": postId
        ])
    }
    
    func trackError(_ error: Error, context: String) {
        logger.error("Error in \(context): \(error.localizedDescription)")
        
        trackEvent(.error, parameters: [
            "error": error.localizedDescription,
            "context": context
        ])
    }
    
    private func sendEvent(_ event: AnalyticsEvent, parameters: [String: Any]) async {
        // Implementation depends on your analytics service
        // Could be Firebase, Mixpanel, custom solution, etc.
    }
}

enum AnalyticsEvent: String {
    case appLaunched = "app_launched"
    case postAction = "post_action"
    case postCreated = "post_created"
    case error = "error"
    case settingsChanged = "settings_changed"
}

enum PostAction: String {
    case viewed = "viewed"
    case approved = "approved"
    case rejected = "rejected"
    case published = "published"
    case edited = "edited"
}
```

This comprehensive implementation plan provides everything needed to successfully transform your Discord bot into professional native iOS and macOS applications while maintaining all existing functionality and adding significant platform-specific enhancements.

The plan emphasizes security, performance, and user experience while providing a clear roadmap for implementation across 16 weeks. Each component is designed to work together seamlessly, creating a robust and scalable system that users will love.