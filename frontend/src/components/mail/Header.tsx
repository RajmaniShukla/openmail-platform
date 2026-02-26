'use client'

import { useState } from 'react'
import {
  RefreshCw,
  MoreVertical,
  Archive,
  Trash2,
  Mail,
  MailOpen,
  Tag,
  MoveRight,
  Sun,
  Moon,
} from 'lucide-react'
import { useEmailStore } from '@/stores/emailStore'
import { emailApi } from '@/lib/api'
import SearchBar from './SearchBar'
import toast from 'react-hot-toast'

export default function Header() {
  const [isDark, setIsDark] = useState(false)
  const {
    selectedEmailIds,
    searchQuery,
    setSearchQuery,
    clearSelection,
    markAsRead,
    markAsUnread,
  } = useEmailStore()

  const hasSelection = selectedEmailIds.length > 0

  const handleBulkAction = async (action: string) => {
    if (selectedEmailIds.length === 0) return

    try {
      await emailApi.bulk({
        email_ids: selectedEmailIds,
        action,
      })

      if (action === 'mark_read') {
        markAsRead(selectedEmailIds)
        toast.success('Marked as read')
      } else if (action === 'mark_unread') {
        markAsUnread(selectedEmailIds)
        toast.success('Marked as unread')
      } else if (action === 'trash') {
        toast.success('Moved to trash')
      } else if (action === 'delete') {
        toast.success('Deleted permanently')
      }

      clearSelection()
    } catch (error) {
      toast.error('Action failed')
    }
  }

  const toggleTheme = () => {
    setIsDark(!isDark)
    document.documentElement.classList.toggle('dark')
  }

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center px-4 gap-4">
      {/* Search */}
      <div className="flex-1 max-w-2xl">
        <SearchBar className="w-full" />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {hasSelection ? (
          <>
            <span className="text-sm text-gray-500 dark:text-gray-400 mr-2">
              {selectedEmailIds.length} selected
            </span>
            <button
              onClick={() => handleBulkAction('mark_read')}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Mark as read"
            >
              <MailOpen className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <button
              onClick={() => handleBulkAction('mark_unread')}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Mark as unread"
            >
              <Mail className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <button
              onClick={() => handleBulkAction('archive')}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Archive"
            >
              <Archive className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <button
              onClick={() => handleBulkAction('trash')}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Delete"
            >
              <Trash2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <button
              onClick={clearSelection}
              className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Toggle theme"
            >
              {isDark ? (
                <Sun className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              ) : (
                <Moon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              )}
            </button>
            <button
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="More options"
            >
              <MoreVertical className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
          </>
        )}
      </div>
    </header>
  )
}
