"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { auth } from "@/lib/auth";
import { localToUtcIso } from "@/lib/format";

export default function ComposePage() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [description, setDescription] = useState("");
  const [generatedText, setGeneratedText] = useState("");
  const [scheduledLocal, setScheduledLocal] = useState("");

  useEffect(() => {
    if (!auth.get()) router.replace("/");
  }, [router]);

  const generate = useMutation({
    mutationFn: () => api.generate(topic, description || undefined),
    onSuccess: (data) => setGeneratedText(data.generated_text),
  });

  const schedule = useMutation({
    mutationFn: () =>
      api.createPost({
        topic,
        description: description || undefined,
        generated_text: generatedText,
        scheduled_at: localToUtcIso(scheduledLocal),
      }),
    onSuccess: () => router.push("/dashboard"),
  });

  const error =
    (generate.error as Error)?.message || (schedule.error as Error)?.message;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Compose a post</h1>
        <p className="mt-1 text-sm text-gray-600">
          1. Enter a topic. 2. Generate a draft. 3. Edit if you want. 4.
          Schedule.
        </p>
      </div>

      <section className="space-y-4 rounded-lg border border-gray-200 bg-white p-6">
        <div>
          <label htmlFor="topic" className="block text-sm font-medium">
            Topic <span className="text-red-500">*</span>
          </label>
          <input
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 p-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="What should this post be about?"
          />
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium">
            Additional context (optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="mt-1 w-full rounded border border-gray-300 p-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Tone, key points, audience…"
          />
        </div>

        <button
          onClick={() => generate.mutate()}
          disabled={!topic.trim() || generate.isPending}
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {generate.isPending
            ? "Generating…"
            : generatedText
              ? "Regenerate draft"
              : "Generate draft"}
        </button>
      </section>

      {generatedText && (
        <section className="space-y-4 rounded-lg border border-gray-200 bg-white p-6">
          <div>
            <label htmlFor="draft" className="block text-sm font-medium">
              Draft (you can edit this)
            </label>
            <textarea
              id="draft"
              value={generatedText}
              onChange={(e) => setGeneratedText(e.target.value)}
              rows={14}
              className="mt-1 w-full rounded border border-gray-300 p-2 font-mono text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              {generatedText.length} characters (LinkedIn limit: 3000)
            </p>
          </div>

          <div>
            <label htmlFor="scheduled" className="block text-sm font-medium">
              Schedule for <span className="text-red-500">*</span>
            </label>
            <input
              id="scheduled"
              type="datetime-local"
              value={scheduledLocal}
              onChange={(e) => setScheduledLocal(e.target.value)}
              className="mt-1 rounded border border-gray-300 p-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Your local time. Will be converted to UTC server-side.
            </p>
          </div>

          <button
            onClick={() => schedule.mutate()}
            disabled={
              !generatedText.trim() ||
              !scheduledLocal ||
              schedule.isPending ||
              generatedText.length > 3000
            }
            className="rounded bg-green-600 px-4 py-2 font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            {schedule.isPending ? "Scheduling…" : "Schedule post"}
          </button>
        </section>
      )}

      {error && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}
    </div>
  );
}
