'use client'

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
  ExternalLink,
  Shield,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react'
import { useEmailStore } from '@/stores/emailStore'
import { emailApi, attachmentApi } from '@/lib/api'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

export default function EmailView() {
  const { selectedEmail, setSelectedEmail, toggleStar } = useEmailStore()

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

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <button
            onClick={handleClose}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 lg:hidden"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
            {selectedEmail.subject || '(no subject)'}
          </h2>
        </div>
        <div className="flex items-center gap-1">
          <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title="Reply">
            <Reply className="w-5 h-5 text-gray-500" />
          </button>
          <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title="Reply All">
            <ReplyAll className="w-5 h-5 text-gray-500" />
          </button>
          <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title="Forward">
            <Forward className="w-5 h-5 text-gray-500" />
          </button>
          <button
            onClick={handleStarClick}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            title="Star"
          >
            <Star
              className={clsx(
                'w-5 h-5',
                selectedEmail.is_starred
                  ? 'fill-yellow-400 text-yellow-400'
                  : 'text-gray-500'
              )}
            />
          </button>
          <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title="Archive">
            <Archive className="w-5 h-5 text-gray-500" />
          </button>
          <button
            onClick={handleDelete}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            title="Delete"
          >
            <Trash2 className="w-5 h-5 text-gray-500" />
          </button>
          <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
            <MoreHorizontal className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Email content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* From/To info */}
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-primary-600 dark:text-primary-400 font-medium text-lg">
              {(selectedEmail.from_name || selectedEmail.from_address)[0].toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-gray-900 dark:text-white">
                {selectedEmail.from_name || selectedEmail.from_address}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                &lt;{selectedEmail.from_address}&gt;
              </span>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              To: {selectedEmail.to_addresses?.map((t: any) => t.name || t.address).join(', ')}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {format(new Date(selectedEmail.date), 'PPpp')}
            </div>
          </div>

          {/* Security indicators */}
          {selectedEmail.security && (
            <div className="flex items-center gap-2">
              {selectedEmail.security.dkim === 'pass' &&
               selectedEmail.security.spf === 'pass' ? (
                <div className="flex items-center gap-1 text-green-600" title="Verified sender">
                  <ShieldCheck className="w-5 h-5" />
                </div>
              ) : (
                <div className="flex items-center gap-1 text-yellow-600" title="Unverified">
                  <ShieldAlert className="w-5 h-5" />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Attachments */}
        {selectedEmail.attachments && selectedEmail.attachments.length > 0 && (
          <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <Paperclip className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {selectedEmail.attachments.length} attachment{selectedEmail.attachments.length > 1 ? 's' : ''}
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedEmail.attachments.map((attachment: any) => (
                <button
                  key={attachment.id}
                  onClick={() => handleDownloadAttachment(attachment)}
                  className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <Download className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-700 dark:text-gray-300 max-w-[150px] truncate">
                    {attachment.filename}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({formatFileSize(attachment.size_bytes)})
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Email body */}
        <div className="email-content">
          {selectedEmail.body_html ? (
            <div dangerouslySetInnerHTML={{ __html: selectedEmail.body_html }} />
          ) : (
            <pre className="whitespace-pre-wrap font-sans text-gray-700 dark:text-gray-300">
              {selectedEmail.body_text || 'No content'}
            </pre>
          )}
        </div>
      </div>

      {/* Quick reply */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Write a quick reply..."
            className="flex-1 input-field"
          />
          <button className="btn-primary">Send</button>
        </div>
      </div>
    </div>
  )
}
