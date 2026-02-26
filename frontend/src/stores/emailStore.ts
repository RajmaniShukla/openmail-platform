import { create } from 'zustand'

interface Email {
  id: string
  thread_id?: string
  from_address: string
  from_name?: string
  to_addresses: Array<{ address: string; name?: string }>
  subject?: string
  snippet?: string
  body_text?: string
  body_html?: string
  date: string
  is_read: boolean
  is_starred: boolean
  has_attachments: boolean
  attachment_count: number
  labels: Array<{ id: string; name: string; color: string }>
  folder?: { id: string; name: string; type: string }
}

interface Folder {
  id: string
  name: string
  type: string
  total_count: number
  unread_count: number
  color?: string
  icon?: string
}

interface Label {
  id: string
  name: string
  color: string
}

interface Mailbox {
  id: string
  full_address: string
  is_primary: boolean
  unread_count: number
}

interface EmailState {
  emails: Email[]
  selectedEmail: Email | null
  selectedEmailIds: string[]
  folders: Folder[]
  labels: Label[]
  mailboxes: Mailbox[]
  currentFolder: string
  currentMailbox: string | null
  isLoading: boolean
  searchQuery: string

  setEmails: (emails: Email[]) => void
  setSelectedEmail: (email: Email | null) => void
  toggleEmailSelection: (id: string) => void
  selectAllEmails: () => void
  clearSelection: () => void
  setFolders: (folders: Folder[]) => void
  setLabels: (labels: Label[]) => void
  setMailboxes: (mailboxes: Mailbox[]) => void
  setCurrentFolder: (folder: string) => void
  setCurrentMailbox: (mailbox: string | null) => void
  setIsLoading: (loading: boolean) => void
  setSearchQuery: (query: string) => void
  markAsRead: (ids: string[]) => void
  markAsUnread: (ids: string[]) => void
  toggleStar: (id: string) => void
}

export const useEmailStore = create<EmailState>((set, get) => ({
  emails: [],
  selectedEmail: null,
  selectedEmailIds: [],
  folders: [],
  labels: [],
  mailboxes: [],
  currentFolder: 'inbox',
  currentMailbox: null,
  isLoading: false,
  searchQuery: '',

  setEmails: (emails) => set({ emails }),
  
  setSelectedEmail: (email) => set({ selectedEmail: email }),
  
  toggleEmailSelection: (id) =>
    set((state) => ({
      selectedEmailIds: state.selectedEmailIds.includes(id)
        ? state.selectedEmailIds.filter((i) => i !== id)
        : [...state.selectedEmailIds, id],
    })),
  
  selectAllEmails: () =>
    set((state) => ({
      selectedEmailIds: state.emails.map((e) => e.id),
    })),
  
  clearSelection: () => set({ selectedEmailIds: [] }),
  
  setFolders: (folders) => set({ folders }),
  
  setLabels: (labels) => set({ labels }),
  
  setMailboxes: (mailboxes) => set({ mailboxes }),
  
  setCurrentFolder: (folder) => set({ currentFolder: folder, selectedEmail: null }),
  
  setCurrentMailbox: (mailbox) => set({ currentMailbox: mailbox }),
  
  setIsLoading: (loading) => set({ isLoading: loading }),
  
  setSearchQuery: (query) => set({ searchQuery: query }),
  
  markAsRead: (ids) =>
    set((state) => ({
      emails: state.emails.map((e) =>
        ids.includes(e.id) ? { ...e, is_read: true } : e
      ),
    })),
  
  markAsUnread: (ids) =>
    set((state) => ({
      emails: state.emails.map((e) =>
        ids.includes(e.id) ? { ...e, is_read: false } : e
      ),
    })),
  
  toggleStar: (id) =>
    set((state) => ({
      emails: state.emails.map((e) =>
        e.id === id ? { ...e, is_starred: !e.is_starred } : e
      ),
    })),
}))
