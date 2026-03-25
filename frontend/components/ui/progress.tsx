"use client"

import * as React from "react"
import { Progress as ProgressPrimitive } from "@base-ui/react/progress"

import { cn } from "@/lib/utils"

function Progress({
  className,
  value,
  ...props
}: ProgressPrimitive.Root.Props & { className?: string }) {
  return (
    <ProgressPrimitive.Root
      data-slot="progress"
      value={value}
      {...props}
    >
      <ProgressPrimitive.Track
        className={cn(
          "relative h-2 w-full overflow-hidden rounded-full bg-muted",
          className
        )}
      >
        <ProgressPrimitive.Indicator
          className="h-full bg-primary transition-all duration-300 ease-in-out rounded-full"
          style={{ width: `${value ?? 0}%` }}
        />
      </ProgressPrimitive.Track>
    </ProgressPrimitive.Root>
  )
}

export { Progress }
