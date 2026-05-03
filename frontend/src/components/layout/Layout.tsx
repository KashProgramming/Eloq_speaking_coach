import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Mic, BarChart2, BookOpen, LogOut, MessageSquare, History, Settings } from 'lucide-react';
import { cn } from '../../utils/cn';

export function Layout() {
  const { logout, user } = useAuth();
  const location = useLocation();

  const navItems = [
    { name: 'Practice', path: '/app/practice', icon: Mic },
    { name: 'Roleplay', path: '/app/roleplay', icon: MessageSquare },
    { name: 'History', path: '/app/history', icon: History },
    { name: 'Progress', path: '/app/progress', icon: BarChart2 },
    { name: 'Settings', path: '/app/settings', icon: Settings },
  ];

  const isActive = (path: string) => {
    return location.pathname.startsWith(path);
  };

  // Extract display name from email (part before @)
  const displayName = user?.email ? user.email.split('@')[0] : 'User';

  return (
    <div className="flex h-screen w-full bg-background dark:bg-dark-background text-textPrimary dark:text-gray-100">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-200 dark:border-gray-800 bg-surface dark:bg-dark-surface p-6 flex flex-col">
        <div className="flex items-center space-x-2 mb-12 cursor-pointer">
          <BookOpen className="h-8 w-8 text-primary" />
          <h1 className="text-2xl font-bold tracking-tight text-textPrimary dark:text-white">Eloq</h1>
        </div>

        <nav className="flex-1 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors font-medium",
                isActive(item.path)
                  ? "bg-primary text-white"
                  : "text-textSecondary hover:bg-gray-100 dark:hover:bg-gray-800 dark:text-gray-400"
              )}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.name}</span>
            </Link>
          ))}
        </nav>

        <div className="mt-auto space-y-3">
          {user?.email && (
            <div className="px-4 py-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <p className="text-xs text-textSecondary uppercase tracking-wide mb-1">Signed in as</p>
              <p className="text-sm font-medium text-textPrimary dark:text-white truncate" title={user.email}>
                {displayName}
              </p>
            </div>
          )}
          <button
            onClick={logout}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-textSecondary hover:bg-gray-100 dark:hover:bg-gray-800 dark:text-gray-400 transition-colors font-medium"
          >
            <LogOut className="h-5 w-5" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto w-full max-w-5xl mx-auto px-12 py-10">
        <Outlet />
      </main>
    </div>
  );
}
