"use client";

import { forwardRef } from "react";
import type { InputHTMLAttributes } from "react";
import clsx from "clsx";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
};

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, error, label, ...props },
  ref,
) {
  return (
    <label className="block space-y-2">
      <span className="text-sm font-medium">{label}</span>
      <input
        ref={ref}
        className={clsx(
          "w-full rounded-2xl border border-border bg-surface-strong px-4 py-3 outline-none transition focus:border-accent",
          error && "border-danger",
          className,
        )}
        {...props}
      />
      {error ? <span className="text-xs text-danger">{error}</span> : null}
    </label>
  );
});
