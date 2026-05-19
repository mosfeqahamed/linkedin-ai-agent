import { auth } from "./auth";
import type {
  AdminPostList,
  AdminStats,
  AdminUser,
  AdminUserList,
  CreatePostInput,
  GenerateResponse,
  MessageResponse,
  Post,
  TokenResponse,
  UpdatePostInput,
  User,
  UserRole,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = auth.get();
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    if (res.status === 401) {
      auth.clear();
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null as T;
  return res.json() as Promise<T>;
}

export const api = {
  register: (email: string, password: string, name?: string) =>
    request<MessageResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name: name || null }),
    }),

  verifyEmail: (email: string, otp: string) =>
    request<TokenResponse>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ email, otp }),
    }),

  resendOtp: (email: string) =>
    request<MessageResponse>("/auth/resend-otp", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  forgotPassword: (email: string) =>
    request<MessageResponse>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  resetPassword: (email: string, otp: string, newPassword: string) =>
    request<TokenResponse>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ email, otp, new_password: newPassword }),
    }),

  me: () => request<User>("/auth/me"),

  linkedinAuthorizeUrl: () =>
    request<{ url: string }>("/auth/linkedin/authorize-url"),

  linkedinDisconnect: () =>
    request<null>("/auth/linkedin/disconnect", { method: "POST" }),

  generate: (input: {
    topic: string;
    description?: string;
    github_url?: string;
    learning_modules?: string[];
  }) =>
    request<GenerateResponse>("/generate", {
      method: "POST",
      body: JSON.stringify({
        topic: input.topic,
        description: input.description || null,
        github_url: input.github_url || null,
        learning_modules: input.learning_modules ?? null,
      }),
    }),

  listPosts: () => request<Post[]>("/posts"),

  getPost: (id: string) => request<Post>(`/posts/${id}`),

  createPost: (data: CreatePostInput) =>
    request<Post>("/posts", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updatePost: (id: string, data: UpdatePostInput) =>
    request<Post>(`/posts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  regeneratePost: (id: string) =>
    request<Post>(`/posts/${id}/regenerate`, { method: "POST" }),

  deletePost: (id: string) =>
    request<null>(`/posts/${id}`, { method: "DELETE" }),

  adminStats: () => request<AdminStats>("/admin/stats"),

  adminListUsers: (search?: string) =>
    request<AdminUserList>(
      `/admin/users${search ? `?search=${encodeURIComponent(search)}` : ""}`,
    ),

  adminUpdateUser: (
    id: string,
    data: { role?: UserRole; is_active?: boolean },
  ) =>
    request<AdminUser>(`/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  adminDeleteUser: (id: string) =>
    request<null>(`/admin/users/${id}`, { method: "DELETE" }),

  adminListPosts: () => request<AdminPostList>("/admin/posts"),
};
