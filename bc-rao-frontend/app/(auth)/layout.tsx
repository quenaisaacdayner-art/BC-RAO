/**
 * Auth layout for login and signup pages.
 * Provides a centered, minimal design outside the main dashboard.
 */

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            BC-RAO
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Social Intelligence for Reddit Marketing
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          {children}
        </div>
      </div>
    </div>
  )
}
