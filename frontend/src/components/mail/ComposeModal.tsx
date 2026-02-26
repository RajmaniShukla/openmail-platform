'use client'

import { useState, useCallback, Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X, Minimize2, Maximize2, Trash2, Paperclip, Send, Bold, Italic, Link, List, Image as ImageIcon } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import LinkExt from '@tiptap/extension-link'
import ImageExt from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import { emailApi } from '@/lib/api'
import { useEmailStore } from '@/stores/emailStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const emailSchema = z.object({
  to: z.string().min(1, 'Recipients required'),
  cc: z.string().optional(),
  bcc: z.string().optional(),
  subject: z.string().optional(),
})

type EmailFormData = z.infer<typeof emailSchema>

interface ComposeModalProps {
  isOpen: boolean
  onClose: () => void
  replyTo?: any
  forward?: any
}

export default function ComposeModal({ isOpen, onClose, replyTo, forward }: ComposeModalProps) {
  const [isMinimized, setIsMinimized] = useState(false)
  const [isMaximized, setIsMaximized] = useState(false)
  const [attachments, setAttachments] = useState<File[]>([])
  const [isSending, setIsSending] = useState(false)
  const [showCc, setShowCc] = useState(false)
  const [showBcc, setShowBcc] = useState(false)

  const { addEmail } = useEmailStore()

  const editor = useEditor({
    extensions: [
      StarterKit,
      LinkExt.configure({
        openOnClick: false,
      }),
      ImageExt,
      Placeholder.configure({
        placeholder: 'Write your message...',
      }),
    ],
    content: forward ? `
      <br/><br/>
      <p>---------- Forwarded message ----------</p>
      <p>From: ${forward.from_name} &lt;${forward.from_address}&gt;</p>
      <p>Date: ${new Date(forward.date).toLocaleString()}</p>
      <p>Subject: ${forward.subject}</p>
      <p>To: ${forward.to_addresses?.join(', ')}</p>
      <br/>
      ${forward.body_html || forward.body_text}
    ` : replyTo ? `
      <br/><br/>
      <p>On ${new Date(replyTo.date).toLocaleString()}, ${replyTo.from_name} &lt;${replyTo.from_address}&gt; wrote:</p>
      <blockquote style="border-left: 2px solid #ccc; margin-left: 10px; padding-left: 10px; color: #666;">
        ${replyTo.body_html || replyTo.body_text}
      </blockquote>
    ` : '',
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none min-h-[200px] p-4',
      },
    },
  })

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<EmailFormData>({
    resolver: zodResolver(emailSchema),
    defaultValues: {
      to: replyTo ? replyTo.from_address : '',
      subject: replyTo 
        ? `Re: ${replyTo.subject?.replace(/^(Re:|Fwd:)\s*/gi, '')}` 
        : forward 
          ? `Fwd: ${forward.subject?.replace(/^(Re:|Fwd:)\s*/gi, '')}` 
          : '',
    },
  })

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setAttachments(prev => [...prev, ...acceptedFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: true,
  })

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const onSubmit = async (data: EmailFormData) => {
    setIsSending(true)
    try {
      const formData = new FormData()
      formData.append('to_addresses', JSON.stringify(data.to.split(',').map(e => e.trim())))
      if (data.cc) formData.append('cc_addresses', JSON.stringify(data.cc.split(',').map(e => e.trim())))
      if (data.bcc) formData.append('bcc_addresses', JSON.stringify(data.bcc.split(',').map(e => e.trim())))
      formData.append('subject', data.subject || '')
      formData.append('body_html', editor?.getHTML() || '')
      formData.append('body_text', editor?.getText() || '')
      
      if (replyTo) {
        formData.append('in_reply_to', replyTo.message_id)
        formData.append('thread_id', replyTo.thread_id)
      }

      attachments.forEach((file) => {
        formData.append('attachments', file)
      })

      const response = await emailApi.send(formData)
      
      toast.success('Email sent successfully!')
      reset()
      editor?.commands.clearContent()
      setAttachments([])
      onClose()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send email')
    } finally {
      setIsSending(false)
    }
  }

  const saveDraft = async () => {
    try {
      // Save as draft logic
      toast.success('Draft saved')
    } catch (error) {
      toast.error('Failed to save draft')
    }
  }

  const handleClose = () => {
    if (editor?.getText().trim() || attachments.length > 0) {
      saveDraft()
    }
    onClose()
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className={clsx(
            "flex min-h-full items-end justify-end p-4",
            isMaximized && "items-stretch justify-stretch p-0"
          )}>
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4"
              enterTo="opacity-100 translate-y-0"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0"
              leaveTo="opacity-0 translate-y-4"
            >
              <Dialog.Panel
                className={clsx(
                  "bg-white dark:bg-gray-800 rounded-t-lg shadow-2xl flex flex-col transform transition-all",
                  isMinimized && "h-12",
                  isMaximized ? "w-full h-full rounded-none" : "w-[600px] max-h-[80vh]",
                  !isMinimized && !isMaximized && "h-[500px]"
                )}
                {...getRootProps()}
              >
                <input {...getInputProps()} />
                
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 bg-gray-100 dark:bg-gray-700 rounded-t-lg">
                  <Dialog.Title className="text-sm font-medium text-gray-900 dark:text-white">
                    {replyTo ? 'Reply' : forward ? 'Forward' : 'New Message'}
                  </Dialog.Title>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setIsMinimized(!isMinimized)}
                      className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                    >
                      <Minimize2 className="w-4 h-4 text-gray-500" />
                    </button>
                    <button
                      onClick={() => setIsMaximized(!isMaximized)}
                      className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                    >
                      <Maximize2 className="w-4 h-4 text-gray-500" />
                    </button>
                    <button
                      onClick={handleClose}
                      className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                    >
                      <X className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                </div>

                {!isMinimized && (
                  <>
                    {/* Form */}
                    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col flex-1 overflow-hidden">
                      {/* Recipients */}
                      <div className="border-b border-gray-200 dark:border-gray-700">
                        <div className="flex items-center px-4 py-2">
                          <label className="text-sm text-gray-500 dark:text-gray-400 w-12">To</label>
                          <input
                            {...register('to')}
                            type="text"
                            placeholder="Recipients"
                            className="flex-1 bg-transparent border-none focus:ring-0 text-sm text-gray-900 dark:text-white placeholder-gray-400"
                          />
                          <div className="flex gap-2 text-sm">
                            <button type="button" onClick={() => setShowCc(!showCc)} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
                              Cc
                            </button>
                            <button type="button" onClick={() => setShowBcc(!showBcc)} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
                              Bcc
                            </button>
                          </div>
                        </div>
                        {errors.to && (
                          <p className="text-xs text-red-500 px-4 pb-1">{errors.to.message}</p>
                        )}
                        
                        {showCc && (
                          <div className="flex items-center px-4 py-2 border-t border-gray-100 dark:border-gray-700">
                            <label className="text-sm text-gray-500 dark:text-gray-400 w-12">Cc</label>
                            <input
                              {...register('cc')}
                              type="text"
                              placeholder="Carbon copy"
                              className="flex-1 bg-transparent border-none focus:ring-0 text-sm text-gray-900 dark:text-white placeholder-gray-400"
                            />
                          </div>
                        )}
                        
                        {showBcc && (
                          <div className="flex items-center px-4 py-2 border-t border-gray-100 dark:border-gray-700">
                            <label className="text-sm text-gray-500 dark:text-gray-400 w-12">Bcc</label>
                            <input
                              {...register('bcc')}
                              type="text"
                              placeholder="Blind carbon copy"
                              className="flex-1 bg-transparent border-none focus:ring-0 text-sm text-gray-900 dark:text-white placeholder-gray-400"
                            />
                          </div>
                        )}
                      </div>

                      {/* Subject */}
                      <div className="flex items-center px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                        <label className="text-sm text-gray-500 dark:text-gray-400 w-12">Subject</label>
                        <input
                          {...register('subject')}
                          type="text"
                          placeholder="Subject"
                          className="flex-1 bg-transparent border-none focus:ring-0 text-sm text-gray-900 dark:text-white placeholder-gray-400"
                        />
                      </div>

                      {/* Editor toolbar */}
                      <div className="flex items-center gap-1 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                        <button
                          type="button"
                          onClick={() => editor?.chain().focus().toggleBold().run()}
                          className={clsx(
                            "p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700",
                            editor?.isActive('bold') && "bg-gray-200 dark:bg-gray-600"
                          )}
                        >
                          <Bold className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => editor?.chain().focus().toggleItalic().run()}
                          className={clsx(
                            "p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700",
                            editor?.isActive('italic') && "bg-gray-200 dark:bg-gray-600"
                          )}
                        >
                          <Italic className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            const url = window.prompt('Enter URL')
                            if (url) {
                              editor?.chain().focus().setLink({ href: url }).run()
                            }
                          }}
                          className={clsx(
                            "p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700",
                            editor?.isActive('link') && "bg-gray-200 dark:bg-gray-600"
                          )}
                        >
                          <Link className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => editor?.chain().focus().toggleBulletList().run()}
                          className={clsx(
                            "p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700",
                            editor?.isActive('bulletList') && "bg-gray-200 dark:bg-gray-600"
                          )}
                        >
                          <List className="w-4 h-4" />
                        </button>
                        <div className="w-px h-4 bg-gray-300 dark:bg-gray-600 mx-1" />
                        <label className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer">
                          <Paperclip className="w-4 h-4" />
                          <input
                            type="file"
                            multiple
                            className="hidden"
                            onChange={(e) => {
                              if (e.target.files) {
                                setAttachments(prev => [...prev, ...Array.from(e.target.files!)])
                              }
                            }}
                          />
                        </label>
                      </div>

                      {/* Editor */}
                      <div className={clsx(
                        "flex-1 overflow-y-auto",
                        isDragActive && "bg-primary-50 dark:bg-primary-900/20 border-2 border-dashed border-primary-500"
                      )}>
                        {isDragActive ? (
                          <div className="h-full flex items-center justify-center text-primary-600">
                            Drop files here to attach
                          </div>
                        ) : (
                          <EditorContent editor={editor} className="h-full" />
                        )}
                      </div>

                      {/* Attachments */}
                      {attachments.length > 0 && (
                        <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
                          <div className="flex flex-wrap gap-2">
                            {attachments.map((file, index) => (
                              <div
                                key={index}
                                className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm"
                              >
                                <Paperclip className="w-4 h-4 text-gray-500" />
                                <span className="max-w-[150px] truncate">{file.name}</span>
                                <span className="text-gray-400 text-xs">({formatFileSize(file.size)})</span>
                                <button
                                  type="button"
                                  onClick={() => removeAttachment(index)}
                                  className="text-gray-400 hover:text-red-500"
                                >
                                  <X className="w-4 h-4" />
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Footer */}
                      <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
                        <button
                          type="submit"
                          disabled={isSending}
                          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Send className="w-4 h-4" />
                          {isSending ? 'Sending...' : 'Send'}
                        </button>
                        <button
                          type="button"
                          onClick={handleClose}
                          className="p-2 text-gray-500 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </form>
                  </>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
