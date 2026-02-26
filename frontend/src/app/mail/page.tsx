'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function MailPage() {
  const router = useRouter()
  
  useEffect(() => {
    // Redirect to inbox by default
    router.replace('/mail/inbox')
  }, [router])
  
  return (
    <div className="h-full flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600"></div>
    </div>
  )
}
