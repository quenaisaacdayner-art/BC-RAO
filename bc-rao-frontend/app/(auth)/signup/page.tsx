/**
 * Signup page.
 * Allows new users to create an account with email and password.
 */

import { SignupForm } from '@/components/forms/signup-form'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Sign up - BC-RAO',
  description: 'Create your BC-RAO account',
}

export default function SignupPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Create your account
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Get started with BC-RAO today
        </p>
      </div>
      <SignupForm />
    </div>
  )
}
