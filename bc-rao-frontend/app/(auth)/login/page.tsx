/**
 * Login page.
 * Allows existing users to authenticate with email and password.
 */

import { LoginForm } from '@/components/forms/login-form'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Log in - BC-RAO',
  description: 'Sign in to your BC-RAO account',
}

export default function LoginPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Welcome back
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Log in to your account
        </p>
      </div>
      <LoginForm />
    </div>
  )
}
