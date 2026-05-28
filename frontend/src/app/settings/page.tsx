'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { 
  User, 
  Mail, 
  Bell, 
  Shield, 
  Palette, 
  Globe, 
  Key, 
  LogOut,
  Save,
  Loader2,
  Plus,
  Trash2,
  ExternalLink,
  ChevronRight,
  Filter
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { userApi, domainApi } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const profileSchema = z.object({
  display_name: z.string().min(1, 'Display name required'),
  timezone: z.string(),
  language: z.string(),
})

const securitySchema = z.object({
  current_password: z.string().min(8, 'Password required'),
  new_password: z.string().min(8, 'Minimum 8 characters'),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
})

const notificationSchema = z.object({
  email_notifications: z.boolean(),
  desktop_notifications: z.boolean(),
  digest_emails: z.enum(['never', 'daily', 'weekly']),
})

type Tab = 'profile' | 'accounts' | 'notifications' | 'security' | 'appearance' | 'domains' | 'filters'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('profile')
  const router = useRouter()
  const queryClient = useQueryClient()
  const { user, logout } = useAuthStore()

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'accounts', label: 'Email Accounts', icon: Mail },
    { id: 'filters', label: 'Filters & Rules', icon: Filter },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'domains', label: 'Domains', icon: Globe },
  ] as const

  return (
    <div className="h-full flex bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Settings</h1>
        <nav className="space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                  activeTab === tab.id
                    ? "bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400"
                    : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                )}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
              </button>
            )
          })}
        </nav>

        <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => {
              logout()
              router.push('/login')
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Sign out
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {activeTab === 'profile' && <ProfileSettings />}
        {activeTab === 'accounts' && <AccountsSettings />}
        {activeTab === 'filters' && <FiltersRedirect />}
        {activeTab === 'notifications' && <NotificationSettings />}
        {activeTab === 'security' && <SecuritySettings />}
        {activeTab === 'appearance' && <AppearanceSettings />}
        {activeTab === 'domains' && <DomainsSettings />}
      </div>
    </div>
  )
}

function ProfileSettings() {
  const { user, updateUser } = useAuthStore()
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      display_name: user?.display_name || '',
      timezone: user?.timezone || 'UTC',
      language: user?.language || 'en',
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: any) => userApi.update(data),
    onSuccess: (response) => {
      updateUser(response.data)
      toast.success('Profile updated')
    },
    onError: () => {
      toast.error('Failed to update profile')
    },
  })

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Profile Settings</h2>
      
      <form onSubmit={handleSubmit((data) => updateMutation.mutate(data))} className="space-y-6">
        {/* Avatar */}
        <div className="flex items-center gap-6">
          <div className="w-20 h-20 rounded-full bg-primary-600 flex items-center justify-center text-white text-2xl font-semibold">
            {user?.display_name?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase()}
          </div>
          <div>
            <button type="button" className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium">
              Change avatar
            </button>
            <p className="text-xs text-gray-500 mt-1">JPG, GIF or PNG. Max size 2MB.</p>
          </div>
        </div>

        {/* Display Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Display Name
          </label>
          <input
            {...register('display_name')}
            type="text"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          {errors.display_name && (
            <p className="text-sm text-red-500 mt-1">{errors.display_name.message}</p>
          )}
        </div>

        {/* Email (read-only) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Email Address
          </label>
          <input
            type="email"
            value={user?.email || ''}
            disabled
            className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400 cursor-not-allowed"
          />
        </div>

        {/* Timezone */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Timezone
          </label>
          <select
            {...register('timezone')}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="UTC">UTC</option>
            <option value="America/New_York">Eastern Time (US & Canada)</option>
            <option value="America/Chicago">Central Time (US & Canada)</option>
            <option value="America/Denver">Mountain Time (US & Canada)</option>
            <option value="America/Los_Angeles">Pacific Time (US & Canada)</option>
            <option value="Europe/London">London</option>
            <option value="Europe/Paris">Paris</option>
            <option value="Asia/Tokyo">Tokyo</option>
            <option value="Asia/Kolkata">India Standard Time</option>
          </select>
        </div>

        {/* Language */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Language
          </label>
          <select
            {...register('language')}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="en">English</option>
            <option value="es">Español</option>
            <option value="fr">Français</option>
            <option value="de">Deutsch</option>
            <option value="ja">日本語</option>
            <option value="zh">中文</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={!isDirty || updateMutation.isPending}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {updateMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Save Changes
        </button>
      </form>
    </div>
  )
}

function AccountsSettings() {
  const { data: mailboxes, isLoading } = useQuery({
    queryKey: ['mailboxes'],
    queryFn: async () => {
      const response = await userApi.getMailboxes()
      return response.data.data || response.data || []
    },
  })

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Email Accounts</h2>
        <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium">
          <Plus className="w-4 h-4" />
          Add Account
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-8">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-gray-400" />
        </div>
      ) : mailboxes?.length > 0 ? (
        <div className="space-y-3">
          {mailboxes.map((mailbox: any) => (
            <div
              key={mailbox.id}
              className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                  <Mail className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">{mailbox.email}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{mailbox.domain}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={clsx(
                  "px-2 py-1 rounded-full text-xs font-medium",
                  mailbox.is_primary
                    ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
                )}>
                  {mailbox.is_primary ? 'Primary' : 'Secondary'}
                </span>
                <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Mail className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <p className="text-gray-500 dark:text-gray-400">No email accounts configured</p>
        </div>
      )}
    </div>
  )
}

function NotificationSettings() {
  const [settings, setSettings] = useState({
    email_notifications: true,
    desktop_notifications: true,
    digest_emails: 'daily' as const,
  })

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Notification Settings</h2>

      <div className="space-y-6">
        <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div>
            <p className="font-medium text-gray-900 dark:text-white">Email Notifications</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Receive notifications about new emails</p>
          </div>
          <button
            onClick={() => setSettings(s => ({ ...s, email_notifications: !s.email_notifications }))}
            className={clsx(
              "relative w-11 h-6 rounded-full transition-colors",
              settings.email_notifications ? "bg-primary-600" : "bg-gray-200 dark:bg-gray-700"
            )}
          >
            <span
              className={clsx(
                "absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform",
                settings.email_notifications && "translate-x-5"
              )}
            />
          </button>
        </div>

        <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div>
            <p className="font-medium text-gray-900 dark:text-white">Desktop Notifications</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Show browser notifications for new emails</p>
          </div>
          <button
            onClick={() => setSettings(s => ({ ...s, desktop_notifications: !s.desktop_notifications }))}
            className={clsx(
              "relative w-11 h-6 rounded-full transition-colors",
              settings.desktop_notifications ? "bg-primary-600" : "bg-gray-200 dark:bg-gray-700"
            )}
          >
            <span
              className={clsx(
                "absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform",
                settings.desktop_notifications && "translate-x-5"
              )}
            />
          </button>
        </div>

        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="font-medium text-gray-900 dark:text-white mb-2">Email Digest</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Receive a summary of your emails</p>
          <select
            value={settings.digest_emails}
            onChange={(e) => setSettings(s => ({ ...s, digest_emails: e.target.value as any }))}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
          >
            <option value="never">Never</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>
      </div>
    </div>
  )
}

function SecuritySettings() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(securitySchema),
  })

  const changePasswordMutation = useMutation({
    mutationFn: (data: any) => userApi.changePassword(data),
    onSuccess: () => {
      toast.success('Password changed successfully')
      reset()
    },
    onError: () => {
      toast.error('Failed to change password')
    },
  })

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Security Settings</h2>

      <div className="space-y-8">
        {/* Change Password */}
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="font-medium text-gray-900 dark:text-white mb-4">Change Password</h3>
          <form onSubmit={handleSubmit((data) => changePasswordMutation.mutate(data))} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Current Password
              </label>
              <input
                {...register('current_password')}
                type="password"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              />
              {errors.current_password && (
                <p className="text-sm text-red-500 mt-1">{errors.current_password.message as string}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                New Password
              </label>
              <input
                {...register('new_password')}
                type="password"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              />
              {errors.new_password && (
                <p className="text-sm text-red-500 mt-1">{errors.new_password.message as string}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Confirm New Password
              </label>
              <input
                {...register('confirm_password')}
                type="password"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              />
              {errors.confirm_password && (
                <p className="text-sm text-red-500 mt-1">{errors.confirm_password.message as string}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={changePasswordMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 font-medium"
            >
              {changePasswordMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Key className="w-4 h-4" />
              )}
              Change Password
            </button>
          </form>
        </div>

        {/* Two-Factor Authentication */}
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">Two-Factor Authentication</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Add an extra layer of security to your account
              </p>
            </div>
            <button className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium">
              Enable 2FA
            </button>
          </div>
        </div>

        {/* Active Sessions */}
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="font-medium text-gray-900 dark:text-white mb-4">Active Sessions</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            These devices are currently logged into your account.
          </p>
          <button className="text-red-600 dark:text-red-400 hover:underline text-sm font-medium">
            Sign out of all other sessions
          </button>
        </div>
      </div>
    </div>
  )
}

function AppearanceSettings() {
  const [theme, setTheme] = useState('system')
  const [density, setDensity] = useState('comfortable')

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Appearance Settings</h2>

      <div className="space-y-6">
        {/* Theme */}
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="font-medium text-gray-900 dark:text-white mb-4">Theme</h3>
          <div className="grid grid-cols-3 gap-3">
            {['light', 'dark', 'system'].map((t) => (
              <button
                key={t}
                onClick={() => setTheme(t)}
                className={clsx(
                  "p-4 rounded-lg border-2 transition-colors text-center capitalize",
                  theme === t
                    ? "border-primary-600 bg-primary-50 dark:bg-primary-900/20"
                    : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                )}
              >
                <div className={clsx(
                  "w-8 h-8 mx-auto mb-2 rounded-full",
                  t === 'light' ? "bg-white border border-gray-200" : t === 'dark' ? "bg-gray-800" : "bg-gradient-to-r from-white to-gray-800"
                )} />
                <span className="text-sm text-gray-700 dark:text-gray-300">{t}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Density */}
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="font-medium text-gray-900 dark:text-white mb-4">Display Density</h3>
          <div className="space-y-2">
            {['comfortable', 'compact', 'cozy'].map((d) => (
              <label key={d} className="flex items-center gap-3 cursor-pointer">
                <input
                  type="radio"
                  name="density"
                  checked={density === d}
                  onChange={() => setDensity(d)}
                  className="w-4 h-4 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-gray-700 dark:text-gray-300 capitalize">{d}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function FiltersRedirect() {
  const router = useRouter()
  
  useEffect(() => {
    router.push('/settings/filters')
  }, [router])
  
  return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
    </div>
  )
}

function DomainsSettings() {
  const queryClient = useQueryClient()
  
  const { data: domains, isLoading } = useQuery({
    queryKey: ['domains'],
    queryFn: async () => {
      const response = await domainApi.list()
      return response.data.data || response.data || []
    },
  })

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Custom Domains</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Add your own domains to send and receive emails
          </p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium">
          <Plus className="w-4 h-4" />
          Add Domain
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-8">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-gray-400" />
        </div>
      ) : domains?.length > 0 ? (
        <div className="space-y-4">
          {domains.map((domain: any) => (
            <div
              key={domain.id}
              className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <Globe className="w-5 h-5 text-gray-400" />
                  <span className="font-medium text-gray-900 dark:text-white">{domain.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={clsx(
                    "px-2 py-1 rounded-full text-xs font-medium",
                    domain.is_verified
                      ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
                      : "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400"
                  )}>
                    {domain.is_verified ? 'Verified' : 'Pending'}
                  </span>
                  <button className="p-1 text-gray-400 hover:text-red-500">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {!domain.is_verified && (
                <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-750 rounded border border-gray-200 dark:border-gray-600">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Add these DNS records to verify your domain:</p>
                  <div className="text-xs font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">
                    <p>MX: mail.{domain.name} (priority: 10)</p>
                    <p>TXT: v=spf1 include:openmail.io ~all</p>
                    <p>DKIM: {domain.dkim_selector}._domainkey.{domain.name}</p>
                  </div>
                  <button className="mt-3 text-sm text-primary-600 dark:text-primary-400 hover:underline">
                    Verify DNS records
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Globe className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <p className="text-gray-500 dark:text-gray-400 mb-4">No custom domains configured</p>
          <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium">
            <Plus className="w-4 h-4" />
            Add your first domain
          </button>
        </div>
      )}
    </div>
  )
}
