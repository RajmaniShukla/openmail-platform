'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Search, 
  Plus, 
  User, 
  Mail, 
  Phone, 
  Building, 
  Star,
  Trash2,
  Edit2,
  MoreVertical,
  Loader2,
  Upload,
  Download
} from 'lucide-react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'
import clsx from 'clsx'

interface Contact {
  id: string
  email: string
  name: string | null
  first_name: string | null
  last_name: string | null
  phone: string | null
  company: string | null
  avatar_url: string | null
  is_favorite: boolean
  frequency: number
  created_at: string
}

export default function ContactsPage() {
  const [search, setSearch] = useState('')
  const [showFavorites, setShowFavorites] = useState(false)
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const queryClient = useQueryClient()

  const { data: contacts, isLoading } = useQuery({
    queryKey: ['contacts', search, showFavorites],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (showFavorites) params.set('favorite', 'true')
      const response = await api.get(`/contacts?${params}`)
      return response.data.data || response.data || []
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/contacts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] })
      setSelectedContact(null)
      toast.success('Contact deleted')
    },
  })

  const toggleFavoriteMutation = useMutation({
    mutationFn: (id: string) => api.post(`/contacts/${id}/favorite`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] })
    },
  })

  const getInitials = (contact: Contact) => {
    if (contact.first_name && contact.last_name) {
      return `${contact.first_name[0]}${contact.last_name[0]}`.toUpperCase()
    }
    if (contact.name) {
      return contact.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
    }
    return contact.email[0].toUpperCase()
  }

  const getDisplayName = (contact: Contact) => {
    if (contact.name) return contact.name
    if (contact.first_name || contact.last_name) {
      return `${contact.first_name || ''} ${contact.last_name || ''}`.trim()
    }
    return contact.email
  }

  return (
    <div className="h-full flex bg-gray-50 dark:bg-gray-900">
      {/* Sidebar - Contact List */}
      <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Contacts</h1>
            <button
              onClick={() => setShowAddModal(true)}
              className="p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search contacts..."
              className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm"
            />
          </div>
          
          {/* Filters */}
          <div className="mt-3 flex gap-2">
            <button
              onClick={() => setShowFavorites(false)}
              className={clsx(
                "px-3 py-1 rounded-full text-sm",
                !showFavorites
                  ? "bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
              )}
            >
              All
            </button>
            <button
              onClick={() => setShowFavorites(true)}
              className={clsx(
                "px-3 py-1 rounded-full text-sm flex items-center gap-1",
                showFavorites
                  ? "bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
              )}
            >
              <Star className="w-3 h-3" /> Favorites
            </button>
          </div>
        </div>

        {/* Contact List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : contacts?.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <User className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No contacts found</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {contacts?.map((contact: Contact) => (
                <button
                  key={contact.id}
                  onClick={() => setSelectedContact(contact)}
                  className={clsx(
                    "w-full p-3 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-750 text-left",
                    selectedContact?.id === contact.id && "bg-primary-50 dark:bg-primary-900/20"
                  )}
                >
                  <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 font-medium">
                    {getInitials(contact)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white truncate">
                      {getDisplayName(contact)}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                      {contact.email}
                    </p>
                  </div>
                  {contact.is_favorite && (
                    <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex gap-2">
            <button className="flex-1 btn-secondary text-sm flex items-center justify-center gap-2">
              <Upload className="w-4 h-4" /> Import
            </button>
            <button className="flex-1 btn-secondary text-sm flex items-center justify-center gap-2">
              <Download className="w-4 h-4" /> Export
            </button>
          </div>
        </div>
      </div>

      {/* Main - Contact Details */}
      <div className="flex-1 overflow-y-auto">
        {selectedContact ? (
          <div className="max-w-2xl mx-auto p-8">
            {/* Header */}
            <div className="flex items-start justify-between mb-8">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 text-2xl font-semibold">
                  {getInitials(selectedContact)}
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {getDisplayName(selectedContact)}
                  </h2>
                  {selectedContact.company && (
                    <p className="text-gray-500 dark:text-gray-400">{selectedContact.company}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleFavoriteMutation.mutate(selectedContact.id)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  <Star
                    className={clsx(
                      "w-5 h-5",
                      selectedContact.is_favorite
                        ? "text-yellow-400 fill-yellow-400"
                        : "text-gray-400"
                    )}
                  />
                </button>
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  <Edit2 className="w-5 h-5 text-gray-400" />
                </button>
                <button
                  onClick={() => {
                    if (confirm('Delete this contact?')) {
                      deleteMutation.mutate(selectedContact.id)
                    }
                  }}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-red-500"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 divide-y divide-gray-200 dark:divide-gray-700">
                <div className="p-4 flex items-center gap-4">
                  <Mail className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Email</p>
                    <a
                      href={`mailto:${selectedContact.email}`}
                      className="text-primary-600 hover:underline"
                    >
                      {selectedContact.email}
                    </a>
                  </div>
                </div>
                {selectedContact.phone && (
                  <div className="p-4 flex items-center gap-4">
                    <Phone className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Phone</p>
                      <a
                        href={`tel:${selectedContact.phone}`}
                        className="text-gray-900 dark:text-white"
                      >
                        {selectedContact.phone}
                      </a>
                    </div>
                  </div>
                )}
                {selectedContact.company && (
                  <div className="p-4 flex items-center gap-4">
                    <Building className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Company</p>
                      <p className="text-gray-900 dark:text-white">{selectedContact.company}</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Quick Actions */}
              <div className="flex gap-3">
                <a
                  href={`mailto:${selectedContact.email}`}
                  className="flex-1 btn-primary flex items-center justify-center gap-2"
                >
                  <Mail className="w-4 h-4" /> Send Email
                </a>
              </div>

              {/* Stats */}
              <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Contact Statistics</p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {selectedContact.frequency}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Emails exchanged</p>
                  </div>
                  <div>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {new Date(selectedContact.created_at).toLocaleDateString()}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Added on</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <User className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">Select a contact to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
