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
  linkedin_post_urn: string | null;
  error_message: string | null;
  publish_attempts: number;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  timezone: string;
  linkedin_connected: boolean;
}

export interface CreatePostInput {
  topic: string;
  description?: string;
  generated_text: string;
  scheduled_at: string;
}

export interface UpdatePostInput {
  generated_text?: string;
  scheduled_at?: string;
}
