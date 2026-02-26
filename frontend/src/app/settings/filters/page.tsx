'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Plus, 
  Filter, 
  Trash2, 
  Edit2, 
  ChevronDown, 
  ChevronUp,
  Inbox,
  Archive,
  Star,
  Tag,
  Loader2,
  AlertCircle,
  Check
} from 'lucide-react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'
import clsx from 'clsx'

interface FilterCondition {
  field: 'from' | 'to' | 'subject' | 'body' | 'has_attachment'
  operator: 'contains' | 'equals' | 'starts_with' | 'ends_with' | 'not_contains'
  value: string
}

interface FilterAction {
  type: 'move' | 'label' | 'star' | 'mark_read' | 'delete' | 'forward'
  value?: string
}

interface EmailFilter {
  id: string
  name: string
  is_active: boolean
  priority: number
  conditions: FilterCondition[]
  actions: FilterAction[]
  stop_processing: boolean
  created_at: string
  match_mode: 'all' | 'any'
}

export default function FiltersPage() {
  const [isCreating, setIsCreating] = useState(false)
  const [editingFilter, setEditingFilter] = useState<EmailFilter | null>(null)
  const queryClient = useQueryClient()

  const { data: filters, isLoading } = useQuery({
    queryKey: ['filters'],
    queryFn: async () => {
      const response = await api.get('/filters')
      return response.data.data || response.data || []
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/filters/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filters'] })
      toast.success('Filter deleted')
    },
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      api.patch(`/filters/${id}`, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filters'] })
    },
  })

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'move': return <Inbox className="w-4 h-4" />
      case 'label': return <Tag className="w-4 h-4" />
      case 'star': return <Star className="w-4 h-4" />
      case 'archive': return <Archive className="w-4 h-4" />
      default: return null
    }
  }

  const getActionDescription = (action: FilterAction) => {
    switch (action.type) {
      case 'move': return `Move to ${action.value}`
      case 'label': return `Add label "${action.value}"`
      case 'star': return 'Star the message'
      case 'mark_read': return 'Mark as read'
      case 'delete': return 'Delete'
      case 'forward': return `Forward to ${action.value}`
      default: return action.type
    }
  }

  const getConditionDescription = (condition: FilterCondition) => {
    const fieldLabels: Record<string, string> = {
      from: 'From',
      to: 'To',
      subject: 'Subject',
      body: 'Body',
      has_attachment: 'Has attachment',
    }
    const operatorLabels: Record<string, string> = {
      contains: 'contains',
      equals: 'equals',
      starts_with: 'starts with',
      ends_with: 'ends with',
      not_contains: 'does not contain',
    }
    return `${fieldLabels[condition.field]} ${operatorLabels[condition.operator]} "${condition.value}"`
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Email Filters</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Create rules to automatically organize your incoming emails
          </p>
        </div>
        <button
          onClick={() => setIsCreating(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Create Filter
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : filters?.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Filter className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No filters yet</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Create your first filter to automatically organize emails
          </p>
          <button
            onClick={() => setIsCreating(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Plus className="w-4 h-4" />
            Create Filter
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filters?.map((filter: EmailFilter) => (
            <FilterCard
              key={filter.id}
              filter={filter}
              onEdit={() => setEditingFilter(filter)}
              onDelete={() => deleteMutation.mutate(filter.id)}
              onToggle={() => toggleMutation.mutate({ id: filter.id, is_active: !filter.is_active })}
              getConditionDescription={getConditionDescription}
              getActionDescription={getActionDescription}
              getActionIcon={getActionIcon}
            />
          ))}
        </div>
      )}

      {/* Create/Edit Modal would go here */}
      {(isCreating || editingFilter) && (
        <FilterModal
          filter={editingFilter}
          onClose={() => {
            setIsCreating(false)
            setEditingFilter(null)
          }}
          onSave={() => {
            queryClient.invalidateQueries({ queryKey: ['filters'] })
            setIsCreating(false)
            setEditingFilter(null)
          }}
        />
      )}
    </div>
  )
}

function FilterCard({
  filter,
  onEdit,
  onDelete,
  onToggle,
  getConditionDescription,
  getActionDescription,
  getActionIcon,
}: {
  filter: EmailFilter
  onEdit: () => void
  onDelete: () => void
  onToggle: () => void
  getConditionDescription: (c: FilterCondition) => string
  getActionDescription: (a: FilterAction) => string
  getActionIcon: (type: string) => React.ReactNode
}) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={clsx(
      "bg-white dark:bg-gray-800 rounded-lg border transition-all",
      filter.is_active
        ? "border-gray-200 dark:border-gray-700"
        : "border-gray-200 dark:border-gray-700 opacity-60"
    )}>
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onToggle}
              className={clsx(
                "w-5 h-5 rounded border flex items-center justify-center",
                filter.is_active
                  ? "bg-primary-600 border-primary-600 text-white"
                  : "border-gray-300 dark:border-gray-600"
              )}
            >
              {filter.is_active && <Check className="w-3 h-3" />}
            </button>
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">{filter.name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {filter.conditions.length} condition{filter.conditions.length !== 1 ? 's' : ''},{' '}
                {filter.actions.length} action{filter.actions.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              {expanded ? (
                <ChevronUp className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              )}
            </button>
            <button
              onClick={onEdit}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              <Edit2 className="w-4 h-4 text-gray-400" />
            </button>
            <button
              onClick={onDelete}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-red-500"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {expanded && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-4">
            {/* Conditions */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Conditions ({filter.match_mode === 'all' ? 'match all' : 'match any'})
              </h4>
              <ul className="space-y-1">
                {filter.conditions.map((condition, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                    <span className="w-1 h-1 bg-gray-400 rounded-full" />
                    {getConditionDescription(condition)}
                  </li>
                ))}
              </ul>
            </div>

            {/* Actions */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Actions</h4>
              <ul className="space-y-1">
                {filter.actions.map((action, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                    {getActionIcon(action.type)}
                    {getActionDescription(action)}
                  </li>
                ))}
              </ul>
            </div>

            {filter.stop_processing && (
              <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400">
                <AlertCircle className="w-4 h-4" />
                Stop processing other filters when this matches
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function FilterModal({
  filter,
  onClose,
  onSave,
}: {
  filter: EmailFilter | null
  onClose: () => void
  onSave: () => void
}) {
  const [name, setName] = useState(filter?.name || '')
  const [matchMode, setMatchMode] = useState<'all' | 'any'>(filter?.match_mode || 'all')
  const [conditions, setConditions] = useState<FilterCondition[]>(
    filter?.conditions || [{ field: 'from', operator: 'contains', value: '' }]
  )
  const [actions, setActions] = useState<FilterAction[]>(
    filter?.actions || [{ type: 'move', value: 'inbox' }]
  )
  const [stopProcessing, setStopProcessing] = useState(filter?.stop_processing || false)
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = async () => {
    if (!name.trim()) {
      toast.error('Please enter a filter name')
      return
    }
    if (conditions.some(c => !c.value)) {
      toast.error('Please fill in all condition values')
      return
    }

    setIsSaving(true)
    try {
      const data = {
        name,
        match_mode: matchMode,
        conditions,
        actions,
        stop_processing: stopProcessing,
        is_active: true,
      }

      if (filter) {
        await api.put(`/filters/${filter.id}`, data)
      } else {
        await api.post('/filters', data)
      }

      toast.success(filter ? 'Filter updated' : 'Filter created')
      onSave()
    } catch (error) {
      toast.error('Failed to save filter')
    } finally {
      setIsSaving(false)
    }
  }

  const addCondition = () => {
    setConditions([...conditions, { field: 'from', operator: 'contains', value: '' }])
  }

  const removeCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index))
  }

  const updateCondition = (index: number, updates: Partial<FilterCondition>) => {
    setConditions(conditions.map((c, i) => (i === index ? { ...c, ...updates } : c)))
  }

  const addAction = () => {
    setActions([...actions, { type: 'label', value: '' }])
  }

  const removeAction = (index: number) => {
    setActions(actions.filter((_, i) => i !== index))
  }

  const updateAction = (index: number, updates: Partial<FilterAction>) => {
    setActions(actions.map((a, i) => (i === index ? { ...a, ...updates } : a)))
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {filter ? 'Edit Filter' : 'Create Filter'}
          </h2>
        </div>

        <div className="p-6 space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Filter Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Filter"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
            />
          </div>

          {/* Match Mode */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Match Mode
            </label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={matchMode === 'all'}
                  onChange={() => setMatchMode('all')}
                  className="text-primary-600"
                />
                <span className="text-sm">Match all conditions</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={matchMode === 'any'}
                  onChange={() => setMatchMode('any')}
                  className="text-primary-600"
                />
                <span className="text-sm">Match any condition</span>
              </label>
            </div>
          </div>

          {/* Conditions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Conditions
            </label>
            <div className="space-y-2">
              {conditions.map((condition, index) => (
                <div key={index} className="flex items-center gap-2">
                  <select
                    value={condition.field}
                    onChange={(e) => updateCondition(index, { field: e.target.value as any })}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  >
                    <option value="from">From</option>
                    <option value="to">To</option>
                    <option value="subject">Subject</option>
                    <option value="body">Body</option>
                  </select>
                  <select
                    value={condition.operator}
                    onChange={(e) => updateCondition(index, { operator: e.target.value as any })}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  >
                    <option value="contains">contains</option>
                    <option value="equals">equals</option>
                    <option value="starts_with">starts with</option>
                    <option value="ends_with">ends with</option>
                    <option value="not_contains">doesn&apos;t contain</option>
                  </select>
                  <input
                    type="text"
                    value={condition.value}
                    onChange={(e) => updateCondition(index, { value: e.target.value })}
                    placeholder="Value"
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  />
                  {conditions.length > 1 && (
                    <button
                      onClick={() => removeCondition(index)}
                      className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={addCondition}
              className="mt-2 text-sm text-primary-600 hover:text-primary-700"
            >
              + Add condition
            </button>
          </div>

          {/* Actions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Actions
            </label>
            <div className="space-y-2">
              {actions.map((action, index) => (
                <div key={index} className="flex items-center gap-2">
                  <select
                    value={action.type}
                    onChange={(e) => updateAction(index, { type: e.target.value as any, value: '' })}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  >
                    <option value="move">Move to folder</option>
                    <option value="label">Add label</option>
                    <option value="star">Star</option>
                    <option value="mark_read">Mark as read</option>
                    <option value="delete">Delete</option>
                    <option value="forward">Forward to</option>
                  </select>
                  {['move', 'label', 'forward'].includes(action.type) && (
                    <input
                      type="text"
                      value={action.value || ''}
                      onChange={(e) => updateAction(index, { value: e.target.value })}
                      placeholder={action.type === 'forward' ? 'email@example.com' : 'Value'}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                    />
                  )}
                  {actions.length > 1 && (
                    <button
                      onClick={() => removeAction(index)}
                      className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={addAction}
              className="mt-2 text-sm text-primary-600 hover:text-primary-700"
            >
              + Add action
            </button>
          </div>

          {/* Stop Processing */}
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={stopProcessing}
              onChange={(e) => setStopProcessing(e.target.checked)}
              className="rounded border-gray-300 text-primary-600"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Stop processing other filters when this matches
            </span>
          </label>
        </div>

        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : filter ? (
              'Update Filter'
            ) : (
              'Create Filter'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
