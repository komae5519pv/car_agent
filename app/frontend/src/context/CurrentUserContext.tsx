import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { authAPI } from '../api'

interface CurrentUser {
  email: string | null
  display_name: string | null
  sales_rep_name: string | null
}

const CurrentUserContext = createContext<CurrentUser>({ email: null, display_name: null, sales_rep_name: null })

export function CurrentUserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser>({ email: null, display_name: null, sales_rep_name: null })

  useEffect(() => {
    authAPI.getMe().then(setUser).catch(() => {})
  }, [])

  return (
    <CurrentUserContext.Provider value={user}>
      {children}
    </CurrentUserContext.Provider>
  )
}

export function useCurrentUser() {
  return useContext(CurrentUserContext)
}
