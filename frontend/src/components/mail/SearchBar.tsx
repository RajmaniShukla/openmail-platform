'use client'

import { useState, useRef, useEffect, Fragment } from 'react'
import { Dialog, Transition, Combobox } from '@headlessui/react'
import { Search, X, Filter, Calendar, User, Tag, Paperclip } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { emailApi } from '@/lib/api'
import { useDebounce } from '@/hooks/useDebounce'
import clsx from 'clsx'

interface SearchResult {
  id: string
  subject: string
  from_name: string
  from_address: string
  snippet: string
  date: string
  folder: string
}

interface SearchBarProps {
  className?: string
}

export default function SearchBar({ className }: SearchBarProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({
    from: '',
    to: '',
    hasAttachment: false,
    dateFrom: '',
    dateTo: '',
    folder: 'all',
    label: '',
  })
  
  const router = useRouter()
  const debouncedQuery = useDebounce(query, 300)
  const inputRef = useRef<HTMLInputElement>(null)

  // Keyboard shortcut to open search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen(true)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Search when query changes
  useEffect(() => {
    if (!debouncedQuery.trim()) {
      setResults([])
      return
    }

    const search = async () => {
      setIsSearching(true)
      try {
        const response = await emailApi.search({
          q: debouncedQuery,
          from: filters.from || undefined,
          to: filters.to || undefined,
          has_attachment: filters.hasAttachment || undefined,
          date_from: filters.dateFrom || undefined,
          date_to: filters.dateTo || undefined,
          folder: filters.folder !== 'all' ? filters.folder : undefined,
        })
        setResults(response.data.data || response.data || [])
      } catch (error) {
        console.error('Search failed:', error)
        setResults([])
      } finally {
        setIsSearching(false)
      }
    }

    search()
  }, [debouncedQuery, filters])

  const handleSelect = (result: SearchResult | null) => {
    if (result) {
      router.push(`/mail/${result.folder}?email=${result.id}`)
      setIsOpen(false)
      setQuery('')
    }
  }

  const buildSearchQuery = () => {
    let parts: string[] = []
    if (query) parts.push(query)
    if (filters.from) parts.push(`from:${filters.from}`)
    if (filters.to) parts.push(`to:${filters.to}`)
    if (filters.hasAttachment) parts.push('has:attachment')
    if (filters.dateFrom) parts.push(`after:${filters.dateFrom}`)
    if (filters.dateTo) parts.push(`before:${filters.dateTo}`)
    return parts.join(' ')
  }

  return (
    <>
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(true)}
        className={clsx(
          "flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors",
          className
        )}
      >
        <Search className="w-4 h-4" />
        <span className="text-sm">Search emails...</span>
        <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 bg-gray-200 dark:bg-gray-600 rounded text-xs">
          <span className="text-xs">⌘</span>K
        </kbd>
      </button>

      {/* Search modal */}
      <Transition appear show={isOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setIsOpen(false)}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-200"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-150"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black/50" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-start justify-center p-4 pt-[15vh]">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-200"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-150"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden transform transition-all">
                  <Combobox value={null} onChange={handleSelect}>
                    {/* Search input */}
                    <div className="flex items-center px-4 border-b border-gray-200 dark:border-gray-700">
                      <Search className="w-5 h-5 text-gray-400" />
                      <Combobox.Input
                        ref={inputRef}
                        className="flex-1 px-4 py-4 bg-transparent border-none focus:ring-0 text-gray-900 dark:text-white placeholder-gray-400"
                        placeholder="Search emails..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        displayValue={() => query}
                      />
                      <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={clsx(
                          "p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700",
                          showFilters && "bg-gray-100 dark:bg-gray-700"
                        )}
                      >
                        <Filter className="w-4 h-4 text-gray-500" />
                      </button>
                      {query && (
                        <button
                          onClick={() => setQuery('')}
                          className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                          <X className="w-4 h-4 text-gray-500" />
                        </button>
                      )}
                    </div>

                    {/* Filters */}
                    {showFilters && (
                      <div className="px-4 py-3 bg-gray-50 dark:bg-gray-750 border-b border-gray-200 dark:border-gray-700">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">From</label>
                            <div className="flex items-center gap-2">
                              <User className="w-4 h-4 text-gray-400" />
                              <input
                                type="text"
                                value={filters.from}
                                onChange={(e) => setFilters(f => ({ ...f, from: e.target.value }))}
                                placeholder="sender@example.com"
                                className="flex-1 px-2 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm"
                              />
                            </div>
                          </div>
                          <div>
                            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">To</label>
                            <div className="flex items-center gap-2">
                              <User className="w-4 h-4 text-gray-400" />
                              <input
                                type="text"
                                value={filters.to}
                                onChange={(e) => setFilters(f => ({ ...f, to: e.target.value }))}
                                placeholder="recipient@example.com"
                                className="flex-1 px-2 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm"
                              />
                            </div>
                          </div>
                          <div>
                            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Date from</label>
                            <div className="flex items-center gap-2">
                              <Calendar className="w-4 h-4 text-gray-400" />
                              <input
                                type="date"
                                value={filters.dateFrom}
                                onChange={(e) => setFilters(f => ({ ...f, dateFrom: e.target.value }))}
                                className="flex-1 px-2 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm"
                              />
                            </div>
                          </div>
                          <div>
                            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Date to</label>
                            <div className="flex items-center gap-2">
                              <Calendar className="w-4 h-4 text-gray-400" />
                              <input
                                type="date"
                                value={filters.dateTo}
                                onChange={(e) => setFilters(f => ({ ...f, dateTo: e.target.value }))}
                                className="flex-1 px-2 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm"
                              />
                            </div>
                          </div>
                          <div className="col-span-2">
                            <label className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={filters.hasAttachment}
                                onChange={(e) => setFilters(f => ({ ...f, hasAttachment: e.target.checked }))}
                                className="rounded border-gray-300 dark:border-gray-600 text-primary-600 focus:ring-primary-500"
                              />
                              <Paperclip className="w-4 h-4 text-gray-400" />
                              <span className="text-sm text-gray-600 dark:text-gray-300">Has attachment</span>
                            </label>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Results */}
                    <Combobox.Options static className="max-h-[400px] overflow-y-auto">
                      {isSearching ? (
                        <div className="py-8 text-center text-gray-500">
                          <div className="animate-spin inline-block w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full mb-2" />
                          <p>Searching...</p>
                        </div>
                      ) : results.length > 0 ? (
                        results.map((result) => (
                          <Combobox.Option
                            key={result.id}
                            value={result}
                            className={({ active }) =>
                              clsx(
                                "px-4 py-3 cursor-pointer",
                                active && "bg-gray-100 dark:bg-gray-700"
                              )
                            }
                          >
                            <div className="flex items-start gap-3">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium text-gray-900 dark:text-white truncate">
                                    {result.from_name || result.from_address}
                                  </span>
                                  <span className="text-xs text-gray-500 dark:text-gray-400">
                                    {new Date(result.date).toLocaleDateString()}
                                  </span>
                                </div>
                                <p className="text-sm text-gray-900 dark:text-white truncate">
                                  {result.subject || '(no subject)'}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                                  {result.snippet}
                                </p>
                              </div>
                              <span className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-600 rounded text-gray-600 dark:text-gray-300">
                                {result.folder}
                              </span>
                            </div>
                          </Combobox.Option>
                        ))
                      ) : query.trim() ? (
                        <div className="py-8 text-center text-gray-500">
                          <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <p>No results found</p>
                          <p className="text-sm">Try adjusting your search or filters</p>
                        </div>
                      ) : (
                        <div className="py-8 text-center text-gray-500">
                          <p className="mb-4">Search tips:</p>
                          <ul className="text-sm text-left inline-block">
                            <li className="mb-1"><code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">from:name</code> - emails from specific sender</li>
                            <li className="mb-1"><code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">to:name</code> - emails to specific recipient</li>
                            <li className="mb-1"><code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">has:attachment</code> - emails with attachments</li>
                            <li><code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">subject:text</code> - search in subject only</li>
                          </ul>
                        </div>
                      )}
                    </Combobox.Options>
                  </Combobox>

                  {/* Footer */}
                  <div className="px-4 py-2 bg-gray-50 dark:bg-gray-750 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 flex items-center gap-4">
                    <span><kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-600 rounded">↑↓</kbd> to navigate</span>
                    <span><kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-600 rounded">↵</kbd> to select</span>
                    <span><kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-600 rounded">esc</kbd> to close</span>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </>
  )
}
