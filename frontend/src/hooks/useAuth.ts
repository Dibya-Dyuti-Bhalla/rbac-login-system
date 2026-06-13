import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../store';
import { RoleName } from '../types';

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector = <T>(selector: (s: RootState) => T) => useSelector(selector);

export const useAuth = () => {
  const user = useAppSelector((s) => s.auth.user);
  const loading = useAppSelector((s) => s.auth.loading);

  const hasRole = (role: RoleName | RoleName[]): boolean => {
    if (!user) return false;
    const roles = Array.isArray(role) ? role : [role];
    return roles.some((r) => user.roles.includes(r)) || user.is_superuser;
  };

  const isAdmin     = hasRole('ADMIN');
  const isUser      = hasRole('USER');
  const isApprover  = hasRole('APPROVER');
  const isPublisher = hasRole('PUBLISHER');

  const primaryRole: RoleName | null = user?.roles?.[0] ?? null;

  return { user, loading, hasRole, isAdmin, isUser, isApprover, isPublisher, primaryRole };
};
