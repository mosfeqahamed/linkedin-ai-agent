import type { InputHTMLAttributes } from "react";

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  id: string;
}

export function Field({ label, id, ...props }: FieldProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      <input
        id={id}
        {...props}
        className="mt-1 w-full rounded border border-gray-300 p-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </div>
  );
}
