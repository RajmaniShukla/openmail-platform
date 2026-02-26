'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Inbox,
  Send,
  FileEdit,
  Trash2,
  AlertCircle,
  Star,
  Archive,
  Tag,
  Settings,
  Plus,
  ChevronDown,
  Mail,
  LogOut,
} from 'lucide-react'
import { useEmailStore } from '@/stores/emailStore'
import { useAuthStore } from '@/stores/authStore'
import { clsx } from 'clsx'
import ComposeModal from './ComposeModal'

const systemFolders = [
  { name: 'Inbox', type: 'inbox', icon: Inbox, href: '/mail/inbox' },
  { name: 'Starred', type: 'starred', icon: Star, href: '/mail/starred' },
  { name: 'Sent', type: 'sent', icon: Send, href: '/mail/sent' },
  { name: 'Drafts', type: 'drafts', icon: FileEdit, href: '/mail/drafts' },
  { name: 'Spam', type: 'spam', icon: AlertCircle, href: '/mail/spam' },
  { name: 'Trash', type: 'trash', icon: Trash2, href: '/mail/trash' },
  { name: 'Archive', type: 'archive', icon: Archive, href: '/mail/archive' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { folders, labels, mailboxes } = useEmailStore()
  const { user, logout } = useAuthStore()
  const [showLabels, setShowLabels] = useState(true)
  const [showCompose, setShowCompose] = useState(false)

  const getFolderCount = (type: string) => {
    const folder = folders.find((f) => f.type === type)
    return folder?.unread_count || 0
  }

  return (
    <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-gray-200 dark:border-gray-700">
        <Link href="/mail/inbox" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <Mail className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-gray-900 dark:text-white">
            OpenMail
          </span>
        </Link>
      </div>

      {/* Compose button */}
      <div className="p-4">
        <button
          onClick={() => setShowCompose(true)}
          className="w-full btn-primary flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Compose
        </button>
      </div>

      {/* Compose Modal */}
      <ComposeModal isOpen={showCompose} onClose={() => setShowCompose(false)} />

      {/* Folders */}
      <nav className="flex-1 overflow-y-auto px-2">
        <div className="space-y-1">
          {systemFolders.map((folder) => {
            const isActive = pathname === folder.href
            const count = getFolderCount(folder.type)
            const Icon = folder.icon

            return (
              <Link
                key={folder.type}
                href={folder.href}
                className={clsx('sidebar-item', isActive && 'active')}
              >
                <Icon className="w-5 h-5" />
                <span className="flex-1">{folder.name}</span>
                {count > 0 && (
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                    {count}
                  </span>
                )}
              </Link>
            )
          })}
        </div>

        {/* Labels */}
        {labels.length > 0 && (
          <div className="mt-6">
            <button
              onClick={() => setShowLabels(!showLabels)}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 w-full"
            >
              <ChevronDown
                className={clsx(
                  'w-4 h-4 transition-transform',
                  !showLabels && '-rotate-90'
                )}
              />
              Labels
            </button>

            {showLabels && (
              <div className="mt-1 space-y-1">
                {labels.map((label) => (
                  <Link
                    key={label.id}
                    href={`/mail/label/${label.id}`}
                    className="sidebar-item"
                  >
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: label.color }}
                    />
                    <span>{label.name}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
            <span className="text-primary-600 dark:text-primary-400 font-medium">
              {user?.first_name?.[0] || user?.email[0].toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {user?.first_name || 'User'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {user?.email}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Link
            href="/settings"
            className="flex-1 btn-secondary text-sm flex items-center justify-center gap-1"
          >
            <Settings className="w-4 h-4" />
            Settings
          </Link>
          <button
            onClick={() => {
              logout()
              router.push('/login')
            }}
            className="btn-secondary text-sm p-2"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}
