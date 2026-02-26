'use client'

import { formatDistanceToNow } from 'date-fns'
import { Star, Paperclip, Check } from 'lucide-react'
import { useEmailStore } from '@/stores/emailStore'
import { emailApi } from '@/lib/api'
import { clsx } from 'clsx'

export default function EmailList() {
  const {
    emails,
    selectedEmail,
    selectedEmailIds,
    isLoading,
    setSelectedEmail,
    toggleEmailSelection,
    selectAllEmails,
    clearSelection,
    toggleStar,
  } = useEmailStore()

  const handleEmailClick = async (email: any) => {
    setSelectedEmail(email)
    
    // Mark as read if unread
    if (!email.is_read) {
      try {
        await emailApi.update(email.id, { is_read: true })
      } catch (error) {
        console.error('Failed to mark as read:', error)
      }
    }
  }

  const handleStarClick = async (e: React.MouseEvent, email: any) => {
    e.stopPropagation()
    try {
      await emailApi.update(email.id, { is_starred: !email.is_starred })
      toggleStar(email.id)
    } catch (error) {
      console.error('Failed to toggle star:', error)
    }
  }

  const handleSelectClick = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    toggleEmailSelection(id)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (emails.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
        <svg className="w-16 h-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
        <p className="text-lg font-medium">No emails</p>
        <p className="text-sm">Your inbox is empty</p>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* List header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-4">
        <button
          onClick={() => selectedEmailIds.length > 0 ? clearSelection() : selectAllEmails()}
          className="w-5 h-5 rounded border border-gray-300 dark:border-gray-600 flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          {selectedEmailIds.length > 0 && (
            <Check className="w-4 h-4 text-primary-600" />
          )}
        </button>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {emails.length} emails
        </span>
      </div>

      {/* Email list */}
      <div className="flex-1 overflow-y-auto">
        {emails.map((email) => {
          const isSelected = selectedEmail?.id === email.id
          const isChecked = selectedEmailIds.includes(email.id)

          return (
            <div
              key={email.id}
              onClick={() => handleEmailClick(email)}
              className={clsx(
                'email-row',
                !email.is_read && 'unread',
                isSelected && 'bg-primary-50 dark:bg-primary-900/20'
              )}
            >
              {/* Checkbox */}
              <button
                onClick={(e) => handleSelectClick(e, email.id)}
                className={clsx(
                  'w-5 h-5 rounded border flex-shrink-0 flex items-center justify-center',
                  isChecked
                    ? 'bg-primary-600 border-primary-600 text-white'
                    : 'border-gray-300 dark:border-gray-600 hover:border-primary-500'
                )}
              >
                {isChecked && <Check className="w-4 h-4" />}
              </button>

              {/* Star */}
              <button
                onClick={(e) => handleStarClick(e, email)}
                className="flex-shrink-0"
              >
                <Star
                  className={clsx(
                    'w-5 h-5',
                    email.is_starred
                      ? 'fill-yellow-400 text-yellow-400'
                      : 'text-gray-300 dark:text-gray-600 hover:text-yellow-400'
                  )}
                />
              </button>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={clsx(
                    'text-sm truncate',
                    email.is_read
                      ? 'text-gray-600 dark:text-gray-400'
                      : 'text-gray-900 dark:text-white font-semibold'
                  )}>
                    {email.from_name || email.from_address}
                  </span>
                  {email.has_attachments && (
                    <Paperclip className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  )}
                  <span className="text-xs text-gray-500 dark:text-gray-400 ml-auto flex-shrink-0">
                    {formatDistanceToNow(new Date(email.date), { addSuffix: true })}
                  </span>
                </div>
                <p className={clsx(
                  'text-sm truncate',
                  email.is_read
                    ? 'text-gray-500 dark:text-gray-500'
                    : 'text-gray-900 dark:text-white'
                )}>
                  {email.subject || '(no subject)'}
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500 truncate">
                  {email.snippet}
                </p>
              </div>

              {/* Labels */}
              {email.labels && email.labels.length > 0 && (
                <div className="flex gap-1 flex-shrink-0">
                  {email.labels.slice(0, 2).map((label: any) => (
                    <span
                      key={label.id}
                      className="label-badge text-white"
                      style={{ backgroundColor: label.color }}
                    >
                      {label.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
