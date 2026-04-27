"use client";

import Link from "next/link";
import { forwardRef } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
  asChild?: boolean;
  children: ReactNode;
};

const variants = {
  primary: "bg-accent text-white hover:bg-accent-strong",
  secondary: "bg-white/60 text-foreground hover:bg-white",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", asChild = false, children, ...props },
  ref,
) {
  const classes = clsx(
    "inline-flex items-center justify-center rounded-full px-5 py-3 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60",
    variants[variant],
    className,
  );

  if (asChild) {
    return <span className={classes}>{children}</span>;
  }

  return (
    <button ref={ref} className={classes} {...props}>
      {children}
    </button>
  );
});

export function ButtonLink({
  href,
  children,
  variant = "primary",
}: {
  href: string;
  children: ReactNode;
  variant?: "primary" | "secondary";
}) {
  return (
    <Link
      href={href}
      className={clsx(
        "inline-flex items-center justify-center rounded-full px-5 py-3 text-sm font-medium transition-colors",
        variants[variant],
      )}
    >
      {children}
    </Link>
  );
}
