/**
 * OpenMail - Email Type Definitions
 */

export interface EmailAddress {
  email: string
  name?: string
}

export interface Attachment {
  id: string
  filename: string
  content_type: string
  size_bytes: number
  content_id?: string
  is_inline: boolean
}

export interface Label {
  id: string
  name: string
  color: string
  description?: string
}

export interface Email {
  id: string
  mailbox_id: string
  folder_id: string
  message_id: string
  thread_id?: string
  in_reply_to?: string
  from_address: string
  from_name?: string
  to_addresses: string[]
  cc_addresses: string[]
  bcc_addresses: string[]
  reply_to?: string
  subject: string
  body_html?: string
  body_text?: string
  snippet: string
  date: string
  is_read: boolean
  is_starred: boolean
  is_draft: boolean
  is_important: boolean
  has_attachments: boolean
  spam_score?: number
  size_bytes: number
  attachments: Attachment[]
  labels: Label[]
  created_at: string
  updated_at: string
}

export interface Folder {
  id: string
  mailbox_id: string
  name: string
  type: FolderType
  parent_id?: string
  color?: string
  icon?: string
  position: number
  is_system: boolean
  unread_count: number
  total_count: number
}

export type FolderType = 
  | 'inbox' 
  | 'sent' 
  | 'drafts' 
  | 'spam' 
  | 'trash' 
  | 'starred' 
  | 'archive' 
  | 'custom'

export interface Mailbox {
  id: string
  user_id: string
  domain_id: string
  email: string
  local_part: string
  display_name?: string
  is_primary: boolean
  is_active: boolean
  quota_bytes: number
  used_bytes: number
  signature_html?: string
  signature_text?: string
  auto_reply_enabled: boolean
  auto_reply_subject?: string
  auto_reply_body?: string
}

export interface Domain {
  id: string
  name: string
  is_verified: boolean
  mx_verified: boolean
  spf_verified: boolean
  dkim_verified: boolean
  dmarc_verified: boolean
  dkim_selector: string
  is_primary: boolean
  is_active: boolean
}

export interface Contact {
  id: string
  user_id: string
  email: string
  name?: string
  first_name?: string
  last_name?: string
  phone?: string
  company?: string
  job_title?: string
  avatar_url?: string
  notes?: string
  is_favorite: boolean
  frequency: number
  last_contacted?: string
  created_at: string
  updated_at: string
}

export interface EmailFilter {
  id: string
  mailbox_id: string
  name: string
  is_active: boolean
  priority: number
  conditions: FilterCondition[]
  actions: FilterAction[]
  match_mode: 'all' | 'any'
  stop_processing: boolean
  created_at: string
  updated_at: string
}

export interface FilterCondition {
  field: 'from' | 'to' | 'subject' | 'body' | 'has_attachment'
  operator: 'contains' | 'equals' | 'starts_with' | 'ends_with' | 'not_contains'
  value: string
}

export interface FilterAction {
  type: 'move' | 'label' | 'star' | 'mark_read' | 'delete' | 'forward'
  value?: string
}

// API Response types
export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface EmailListParams {
  folder?: string
  folder_id?: string
  label_id?: string
  is_read?: boolean
  is_starred?: boolean
  has_attachments?: boolean
  search?: string
  skip?: number
  limit?: number
}

export interface EmailSearchParams {
  q?: string
  from?: string
  to?: string
  has_attachment?: boolean
  date_from?: string
  date_to?: string
  folder?: string
  limit?: number
}

// Stats types
export interface OverviewStats {
  total_emails: number
  unread_emails: number
  starred_emails: number
  draft_emails: number
  sent_today: number
  received_today: number
  spam_count: number
  storage_used_bytes: number
}

export interface ActivityData {
  date: string
  sent: number
  received: number
}

export interface TopSender {
  email: string
  name?: string
  count: number
}
