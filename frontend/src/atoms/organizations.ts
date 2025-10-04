import { atom } from 'jotai'

export interface Organization {
  org_id: string
  name: string // slug (URL-safe identifier)
  display_name: string // human-readable name
  description?: string
  created_at: string
}

// Organizations atom (array data)
export const organizationsAtom = atom<Organization[]>([])
