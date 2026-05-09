import { auth } from "./auth";
import type { CreatePostInput, Post, UpdatePostInput, User } from "./types";

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
  devLogin: (email: string, name?: string) =>
    request<{ access_token: string; token_type: string }>("/auth/dev-login", {
      method: "POST",
      body: JSON.stringify({ email, name: name || null }),
    }),

  me: () => request<User>("/auth/me"),

  linkedinAuthorizeUrl: () =>
    request<{ url: string }>("/auth/linkedin/authorize-url"),

  linkedinDisconnect: () =>
    request<null>("/auth/linkedin/disconnect", { method: "POST" }),

  generate: (topic: string, description?: string) =>
    request<{ generated_text: string }>("/generate", {
      method: "POST",
      body: JSON.stringify({ topic, description: description || null }),
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
};
