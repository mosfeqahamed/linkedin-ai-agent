/**
 * Convert a `<input type="datetime-local">` value (e.g. "2026-05-10T22:00")
 * — interpreted in the user's local timezone — to a UTC ISO string the API expects.
 */
export function localToUtcIso(localDateTime: string): string {
  return new Date(localDateTime).toISOString();
}

/**
 * Convert a UTC ISO string back to the format expected by `<input type="datetime-local">`.
 */
export function utcToLocalDateTimeInput(utcIso: string): string {
  const d = new Date(utcIso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  );
}

export function formatDateTime(utcIso: string): string {
  return new Date(utcIso).toLocaleString();
}

export function relativeTime(utcIso: string): string {
  const diff = new Date(utcIso).getTime() - Date.now();
  const abs = Math.abs(diff);
  const minutes = Math.round(abs / 60000);
  const hours = Math.round(minutes / 60);
  const days = Math.round(hours / 24);

  const fmt = (n: number, unit: string) => `${n} ${unit}${n === 1 ? "" : "s"}`;
  let label: string;
  if (minutes < 1) label = "just now";
  else if (minutes < 60) label = fmt(minutes, "minute");
  else if (hours < 24) label = fmt(hours, "hour");
  else label = fmt(days, "day");

  return diff > 0 ? `in ${label}` : `${label} ago`;
}
