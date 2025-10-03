import { atom } from 'jotai'

// Individual atoms for user fields (required for hydration-test-utils)
export const userIdAtom = atom<number | null>(null)
export const userEmailAtom = atom<string | null>(null)
export const userOrgIdAtom = atom<number | null>(null)
export const userOrganizationNameAtom = atom<string | null>(null)
export const userRoleAtom = atom<'owner' | 'admin' | 'member' | 'super_admin' | null>(null)
export const userFirebaseUidAtom = atom<string | null>(null)

// Derived atom for convenience (computed from individual atoms)
export const userAtom = atom((get) => {
  const id = get(userIdAtom)
  if (id === null) return null

  return {
    id,
    email: get(userEmailAtom)!,
    orgId: get(userOrgIdAtom),
    organizationName: get(userOrganizationNameAtom),
    role: get(userRoleAtom)!,
    firebaseUid: get(userFirebaseUidAtom)!,
  }
})
