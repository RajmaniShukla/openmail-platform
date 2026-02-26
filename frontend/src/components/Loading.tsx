'use client'

import { Loader2, Mail } from 'lucide-react'
import clsx from 'clsx'

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  fullScreen?: boolean
}

export default function Loading({ size = 'md', text, fullScreen = false }: LoadingProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }

  const content = (
    <div className="flex flex-col items-center justify-center gap-3">
      <Loader2 className={clsx('animate-spin text-primary-600', sizeClasses[size])} />
      {text && (
        <p className="text-sm text-gray-500 dark:text-gray-400">{text}</p>
      )}
    </div>
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white dark:bg-gray-900 flex items-center justify-center z-50">
        {content}
      </div>
    )
  }

  return content
}

export function PageLoading() {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 dark:bg-primary-900/30 rounded-full mb-4">
          <Mail className="w-8 h-8 text-primary-600 animate-pulse" />
        </div>
        <Loader2 className="w-6 h-6 animate-spin text-primary-600 mx-auto" />
      </div>
    </div>
  )
}

export function InlineLoading({ text = 'Loading...' }: { text?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-gray-500 dark:text-gray-400">
      <Loader2 className="w-4 h-4 animate-spin" />
      {text}
    </span>
  )
}
