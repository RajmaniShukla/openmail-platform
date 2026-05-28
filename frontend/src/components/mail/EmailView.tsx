'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import {
  X,
  Reply,
  ReplyAll,
  Forward,
  Star,
  Archive,
  Trash2,
  MoreHorizontal,
  Paperclip,
  Download,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react'
import { useEmailStore } from '@/stores/emailStore'
import { emailApi, attachmentApi } from '@/lib/api'
import { useEmailThread } from '@/hooks/useEmailThread'
import ComposeModal from '@/components/mail/ComposeModal'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

export default function EmailView() {
  const { selectedEmail, setSelectedEmail, toggleStar } = useEmailStore()
  const [composeMode, setComposeMode] = useState<null | 'reply' | 'replyAll' | 'forward'>(null)
  const [collapsedIds, setCollapsedIds] = useState<Set<string>>(new Set())

  const { data: threadEmails } = useEmailThread(selectedEmail)
  // If we got thread data use it; otherwise show just the selected email
  const emails = threadEmails && threadEmails.length > 1 ? threadEmails : (selectedEmail ? [selectedEmail] : [])

  if (!selectedEmail) return null

  const handleClose = () => setSelectedEmail(null)

  const handleStarClick = async () => {
    try {
      await emailApi.update(selectedEmail.id, { is_starred: !selectedEmail.is_starred })
      toggleStar(selectedEmail.id)
    } catch (error) {
      toast.error('Failed to update')
    }
  }

  const handleDelete = async () => {
    try {
      await emailApi.delete(selectedEmail.id)
      toast.success('Moved to trash')
      setSelectedEmail(null)
    } catch (error) {
      toast.error('Failed to delete')
    }
  }

  const handleDownloadAttachment = async (attachment: any) => {
    try {
      const response = await attachmentApi.download(attachment.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', attachment.filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      toast.error('Failed to download')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const toggleCollapse = (id: string) => {
    setCollapsedIds((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <button onClick={handleClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 lg:hidden">
            <X className="w-5 h-5 text-gray-500" />
          </button>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {selectedEmail.subject || '(no subject)'}
            </h2>
            {emails.length > 1 && (
              <span className="text-xs text-gray-400">{emails.length} messages in thread</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => setComposeMode('reply')} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title="Reply">
            <Reply className="w-5 h-5 text-gray-500" />
          </button>
          <button onClick={() => setComposeMode('replyAll')} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title="Reply All">
            <ReplyAll className="w-5 h-5 text-gray-500" />
          </button>
          <button onClick={() => setComposeMode('forward')} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title="Forward">
            <Forward className="w-5 h-5 text-gray-500" />
          </button>
          <button onClick={handleStarClick} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title="Star">
            <Star className={clsx('w-5 h-5', selectedEmail.is_starred ? 'fill-yellow-400 text-yellow-400' : 'text-gray-500')} />
          </button>
          <button onClick={handleDelete} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title="Delete">
            <Trash2 className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Thread messages */}
      <div className="flex-1 overflow-y-auto">
        {emails.map((email: any, idx: number) => {
          const isLast = idx === emails.length - 1
          const isCollapsed = collapsedIds.has(email.id)

          return (
            <div key={email.id} className={clsx('border-b border-gray-100 dark:border-gray-700', isLast && 'border-none')}>
              {/* Message header — always visible */}
              <button
                onClick={() => !isLast && toggleCollapse(email.id)}
                className={clsx(
                  'w-full flex items-center gap-4 px-6 py-4 text-left',
                  !isLast && 'hover:bg-gray-50 dark:hover:bg-gray-700/30 cursor-pointer',
                  isLast && 'cursor-default'
                )}
              >
                <div className="w-9 h-9 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center flex-shrink-0 text-indigo-600 dark:text-indigo-300 font-semibold text-sm">
                  {(email.from_name || email.from_address || '?')[0].toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 dark:text-white text-sm">
                      {email.from_name || email.from_address}
                    </span>
                    {email.security?.dkim === 'pass' && email.security?.spf === 'pass' ? (
                      <ShieldCheck className="w-3.5 h-3.5 text-green-500" aria-label="Verified" />
                    ) : null}
                    {email.has_attachments && <Paperclip className="w-3.5 h-3.5 text-gray-400" />}
                  </div>
                  {isCollapsed && (
                    <p className="text-xs text-gray-500 truncate">{email.snippet}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-xs text-gray-400">{format(new Date(email.date), 'PPp')}</span>
                  {!isLast && (isCollapsed
                    ? <ChevronDown className="w-4 h-4 text-gray-400" />
                    : <ChevronUp className="w-4 h-4 text-gray-400" />)
                  }
                </div>
              </button>

              {/* Message body — shown when not collapsed */}
              {!isCollapsed && (
                <div className="px-6 pb-6">
                  {/* To line */}
                  <p className="text-xs text-gray-400 mb-4">
                    To: {email.to_addresses?.map((t: any) => t.name || t.address).join(', ')}
                  </p>

                  {/* Attachments */}
                  {email.attachments && email.attachments.length > 0 && (
                    <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg flex flex-wrap gap-2">
                      {email.attachments.map((att: any) => (
                        <button
                          key={att.id}
                          onClick={() => handleDownloadAttachment(att)}
                          className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
                        >
                          <Download className="w-3.5 h-3.5 text-gray-500" />
                          <span className="max-w-[140px] truncate text-gray-700 dark:text-gray-300">{att.filename}</span>
                          <span className="text-xs text-gray-400">({formatFileSize(att.size_bytes)})</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Body */}
                  <div className="email-content prose prose-sm dark:prose-invert max-w-none">
                    {email.body_html ? (
                      <div dangerouslySetInnerHTML={{ __html: email.body_html }} />
                    ) : (
                      <pre className="whitespace-pre-wrap font-sans text-gray-700 dark:text-gray-300 text-sm">
                        {email.body_text || 'No content'}
                      </pre>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Reply / Forward modals */}
      {composeMode && (
        <ComposeModal
          isOpen={!!composeMode}
          onClose={() => setComposeMode(null)}
          replyTo={composeMode === 'reply' || composeMode === 'replyAll' ? selectedEmail : undefined}
          forward={composeMode === 'forward' ? selectedEmail : undefined}
        />
      )}
    </div>
  )
}
