export type PostStatus =
  | "draft"
  | "scheduled"
  | "publishing"
  | "published"
  | "failed"
  | "cancelled";

export interface Post {
  id: string;
  topic: string;
  description: string | null;
  generated_text: string;
  scheduled_at: string;
  status: PostStatus;
  repo_url: string | null;
  repo_summary: string | null;
  learning_modules: string[];
  linkedin_post_urn: string | null;
  error_message: string | null;
  publish_attempts: number;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export interface GenerateResponse {
  generated_text: string;
  repo_summary: string | null;
  tech_stack: string[];
  learning_modules: string[];
}

export type UserRole = "user" | "admin";

export interface User {
  id: string;
  email: string;
  name: string | null;
  role: UserRole;
  is_verified: boolean;
  timezone: string;
  linkedin_connected: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface MessageResponse {
  message: string;
}

export interface AdminUser {
  id: string;
  email: string;
  name: string | null;
  role: UserRole;
  is_verified: boolean;
  is_active: boolean;
  linkedin_connected: boolean;
  created_at: string;
  post_count: number | null;
}

export interface AdminUserList {
  users: AdminUser[];
  total: number;
}

export interface AdminStats {
  total_users: number;
  verified_users: number;
  admins: number;
  linkedin_connected: number;
  total_posts: number;
  posts_by_status: Record<string, number>;
}

export interface AdminPost {
  id: string;
  user_id: string;
  user_email: string | null;
  topic: string;
  status: PostStatus;
  scheduled_at: string;
  created_at: string;
  error_message: string | null;
}

export interface AdminPostList {
  posts: AdminPost[];
  total: number;
}

export interface CreatePostInput {
  topic: string;
  description?: string;
  generated_text: string;
  scheduled_at: string;
  repo_url?: string;
  repo_summary?: string;
  learning_modules?: string[];
}

export interface UpdatePostInput {
  generated_text?: string;
  scheduled_at?: string;
}
