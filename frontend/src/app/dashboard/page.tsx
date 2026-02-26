'use client'

import { useQuery } from '@tanstack/react-query'
import { 
  Inbox, 
  Send, 
  Star, 
  Trash2,
  TrendingUp,
  TrendingDown,
  Mail,
  Users,
  HardDrive,
  Activity,
  Loader2
} from 'lucide-react'
import { api } from '@/lib/api'
import Link from 'next/link'
import clsx from 'clsx'

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', 'overview'],
    queryFn: async () => {
      const response = await api.get('/stats/overview')
      return response.data
    },
  })

  const { data: activity, isLoading: activityLoading } = useQuery({
    queryKey: ['stats', 'activity'],
    queryFn: async () => {
      const response = await api.get('/stats/activity?days=7')
      return response.data.activity || []
    },
  })

  const { data: topSenders, isLoading: sendersLoading } = useQuery({
    queryKey: ['stats', 'top-senders'],
    queryFn: async () => {
      const response = await api.get('/stats/top-senders?limit=5')
      return response.data.senders || []
    },
  })

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const statCards = [
    {
      label: 'Total Emails',
      value: stats?.total_emails || 0,
      icon: Mail,
      color: 'bg-blue-500',
      href: '/mail/inbox',
    },
    {
      label: 'Unread',
      value: stats?.unread_emails || 0,
      icon: Inbox,
      color: 'bg-red-500',
      href: '/mail/inbox',
    },
    {
      label: 'Starred',
      value: stats?.starred_emails || 0,
      icon: Star,
      color: 'bg-yellow-500',
      href: '/mail/starred',
    },
    {
      label: 'Sent Today',
      value: stats?.sent_today || 0,
      icon: Send,
      color: 'bg-green-500',
      href: '/mail/sent',
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Dashboard</h1>

        {/* Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {statCards.map((stat) => {
            const Icon = stat.icon
            return (
              <Link
                key={stat.label}
                href={stat.href}
                className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{stat.label}</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                      {statsLoading ? '-' : stat.value.toLocaleString()}
                    </p>
                  </div>
                  <div className={clsx("p-3 rounded-lg", stat.color)}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                </div>
              </Link>
            )
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Activity Chart */}
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary-600" />
              Email Activity (Last 7 Days)
            </h2>
            
            {activityLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="space-y-3">
                {activity?.map((day: any) => {
                  const total = day.sent + day.received
                  const maxTotal = Math.max(...activity.map((d: any) => d.sent + d.received)) || 1
                  
                  return (
                    <div key={day.date} className="flex items-center gap-4">
                      <span className="text-sm text-gray-500 dark:text-gray-400 w-20">
                        {new Date(day.date).toLocaleDateString('en', { weekday: 'short', month: 'short', day: 'numeric' })}
                      </span>
                      <div className="flex-1 flex gap-1">
                        <div
                          className="h-6 bg-green-500 rounded-l"
                          style={{ width: `${(day.sent / maxTotal) * 50}%` }}
                          title={`Sent: ${day.sent}`}
                        />
                        <div
                          className="h-6 bg-blue-500 rounded-r"
                          style={{ width: `${(day.received / maxTotal) * 50}%` }}
                          title={`Received: ${day.received}`}
                        />
                      </div>
                      <span className="text-sm text-gray-600 dark:text-gray-300 w-16 text-right">
                        {total} emails
                      </span>
                    </div>
                  )
                })}
                <div className="flex gap-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <span className="flex items-center gap-2 text-sm text-gray-500">
                    <div className="w-3 h-3 bg-green-500 rounded" /> Sent
                  </span>
                  <span className="flex items-center gap-2 text-sm text-gray-500">
                    <div className="w-3 h-3 bg-blue-500 rounded" /> Received
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar Stats */}
          <div className="space-y-6">
            {/* Storage */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <HardDrive className="w-5 h-5 text-primary-600" />
                Storage
              </h2>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Used</span>
                  <span className="text-gray-900 dark:text-white font-medium">
                    {statsLoading ? '-' : formatBytes(stats?.storage_used_bytes || 0)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-primary-600 h-2 rounded-full" 
                    style={{ width: `${Math.min((stats?.storage_used_bytes || 0) / (5 * 1024 * 1024 * 1024) * 100, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  of 5 GB quota
                </p>
              </div>
            </div>

            {/* Top Senders */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-primary-600" />
                Top Senders
              </h2>
              
              {sendersLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                </div>
              ) : topSenders?.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                  No data yet
                </p>
              ) : (
                <ul className="space-y-3">
                  {topSenders?.map((sender: any, index: number) => (
                    <li key={sender.email} className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-xs font-medium text-primary-600">
                        {index + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {sender.name || sender.email}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {sender.email}
                        </p>
                      </div>
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {sender.count}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Quick Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Quick Actions
              </h2>
              <div className="space-y-2">
                <Link
                  href="/mail/inbox"
                  className="w-full btn-secondary flex items-center justify-center gap-2"
                >
                  <Inbox className="w-4 h-4" /> Go to Inbox
                </Link>
                <Link
                  href="/contacts"
                  className="w-full btn-secondary flex items-center justify-center gap-2"
                >
                  <Users className="w-4 h-4" /> Manage Contacts
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
