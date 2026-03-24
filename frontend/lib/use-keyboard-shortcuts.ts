"use client";

import { useEffect } from "react";

export function useKeyboardShortcuts() {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Don't trigger when typing in inputs
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) return;

      if (e.key === "/" && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        const searchInput = document.querySelector<HTMLInputElement>('input[placeholder*="Search"], input[placeholder*="search"]');
        searchInput?.focus();
      }

      if (e.key === "Escape") {
        const closeButton = document.querySelector<HTMLButtonElement>('[data-dialog-close], [aria-label="Close"]');
        closeButton?.click();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);
}
