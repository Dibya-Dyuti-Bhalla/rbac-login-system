import React, { useState } from 'react';
import {
  Box, Drawer, AppBar, Toolbar, Typography, List, ListItem,
  ListItemButton, ListItemIcon, ListItemText, IconButton, Avatar,
  Badge, Tooltip, Divider, Chip, Menu, MenuItem,
} from '@mui/material';
import {
  Dashboard, People, Article, CheckCircle, Publish, Settings,
  Notifications, Logout, Menu as MenuIcon, Assignment,
  BarChart, History, SmartToy, CloudSync, Pending, Block,
  VerifiedUser,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth, useAppDispatch, useAppSelector } from '../../hooks/useAuth';
import { logout, fetchNotifications } from '../../store';
import { ROLE_COLORS } from '../../theme';

const DRAWER_WIDTH = 240;

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  roles?: string[];
}

const NAV_ITEMS: NavItem[] = [
  // Admin
  { label: 'Dashboard',      path: '/dashboard',            icon: <Dashboard />,   roles: [] },
  { label: 'User Management',path: '/admin/users',          icon: <People />,      roles: ['ADMIN'] },
  { label: 'Audit Logs',     path: '/admin/audit',          icon: <History />,     roles: ['ADMIN'] },
  { label: 'Platform Stats', path: '/admin/stats',          icon: <BarChart />,    roles: ['ADMIN'] },
  // User
  { label: 'My Articles',    path: '/articles/mine',        icon: <Article />,     roles: ['USER'] },
  { label: 'Generate Article',path: '/articles/generate',   icon: <SmartToy />,    roles: ['USER'] },
  { label: 'Source & Sync',  path: '/source-sync',          icon: <CloudSync />,   roles: ['USER'] },
  { label: 'Pipeline Review',path: '/pipeline',             icon: <Assignment />,  roles: ['USER'] },
  // Approver
  { label: 'Pending Review', path: '/approver/pending',     icon: <Pending />,     roles: ['APPROVER'] },
  { label: 'Approved',       path: '/approver/approved',    icon: <CheckCircle />, roles: ['APPROVER'] },
  { label: 'Rejected',       path: '/approver/rejected',    icon: <Block />,       roles: ['APPROVER'] },
  // Publisher
  { label: 'Publish Queue',  path: '/publisher/queue',      icon: <Publish />,     roles: ['PUBLISHER'] },
  { label: 'Published',      path: '/publisher/published',  icon: <VerifiedUser />,roles: ['PUBLISHER'] },
];

interface Props { children: React.ReactNode }

export const AppLayout: React.FC<Props> = ({ children }) => {
  const { user, hasRole } = useAuth();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const unread = useAppSelector((s) => s.notif.unread_count);

  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const visibleNav = NAV_ITEMS.filter(
    (item) => item.roles!.length === 0 || item.roles!.some((r) => hasRole(r as any))
  );

  const handleLogout = async () => {
    await dispatch(logout());
    navigate('/login');
  };

  React.useEffect(() => {
    dispatch(fetchNotifications());
  }, []);

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Brand */}
      <Box sx={{ p: 2.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Box sx={{
          width: 36, height: 36, borderRadius: 1.5,
          background: 'linear-gradient(135deg, #6366f1, #e2b96f)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Typography fontWeight={800} color="white" fontSize={14}>KB</Typography>
        </Box>
        <Box>
          <Typography fontWeight={700} fontSize={15} lineHeight={1.2}>KBG Platform</Typography>
          <Typography fontSize={11} color="text.secondary">Knowledge Base Generator</Typography>
        </Box>
      </Box>
      <Divider />

      {/* Role badge */}
      {user && (
        <Box sx={{ px: 2, py: 1.5 }}>
          {user.roles.map((r) => (
            <Chip
              key={r}
              label={r}
              size="small"
              sx={{ mr: 0.5, mb: 0.5, bgcolor: ROLE_COLORS[r] + '22', color: ROLE_COLORS[r], fontWeight: 700, fontSize: 10 }}
            />
          ))}
        </Box>
      )}

      {/* Nav */}
      <List sx={{ flex: 1, px: 1 }}>
        {visibleNav.map((item) => {
          const active = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.25 }}>
              <ListItemButton
                onClick={() => { navigate(item.path); setMobileOpen(false); }}
                selected={active}
                sx={{
                  borderRadius: 2,
                  '&.Mui-selected': {
                    bgcolor: 'primary.main',
                    color: 'white',
                    '& .MuiListItemIcon-root': { color: 'white' },
                    '&:hover': { bgcolor: 'primary.dark' },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 36, color: active ? 'inherit' : 'text.secondary' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{ fontSize: 13.5, fontWeight: active ? 600 : 400 }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Divider />
      {/* User */}
      <Box sx={{ p: 1.5 }}>
        <ListItemButton
          onClick={(e) => setAnchorEl(e.currentTarget)}
          sx={{ borderRadius: 2 }}
        >
          <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', fontSize: 13, mr: 1.5 }}>
            {user?.full_name?.[0]?.toUpperCase()}
          </Avatar>
          <Box sx={{ minWidth: 0 }}>
            <Typography fontSize={13} fontWeight={600} noWrap>{user?.full_name}</Typography>
            <Typography fontSize={11} color="text.secondary" noWrap>{user?.email}</Typography>
          </Box>
        </ListItemButton>
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
          <MenuItem onClick={handleLogout}>
            <Logout fontSize="small" sx={{ mr: 1 }} /> Logout
          </MenuItem>
        </Menu>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Mobile AppBar */}
      <AppBar position="fixed" sx={{ display: { md: 'none' } }}>
        <Toolbar>
          <IconButton color="inherit" onClick={() => setMobileOpen(true)} edge="start">
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flex: 1 }}>KBG Platform</Typography>
          <IconButton color="inherit" onClick={() => navigate('/notifications')}>
            <Badge badgeContent={unread} color="error"><Notifications /></Badge>
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Desktop AppBar */}
      <AppBar position="fixed" sx={{ display: { xs: 'none', md: 'block' }, left: DRAWER_WIDTH, width: `calc(100% - ${DRAWER_WIDTH}px)` }}>
        <Toolbar sx={{ justifyContent: 'flex-end' }}>
          <Tooltip title="Notifications">
            <IconButton color="inherit" onClick={() => navigate('/notifications')}>
              <Badge badgeContent={unread} color="error"><Notifications /></Badge>
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Sidebar - mobile */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        ModalProps={{ keepMounted: true }}
        sx={{ display: { xs: 'block', md: 'none' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}
      >
        {drawer}
      </Drawer>

      {/* Sidebar - desktop */}
      <Drawer
        variant="permanent"
        sx={{ display: { xs: 'none', md: 'block' }, width: DRAWER_WIDTH, flexShrink: 0, '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}
      >
        {drawer}
      </Drawer>

      {/* Main content */}
      <Box component="main" sx={{ flex: 1, p: 3, pt: { xs: 10, md: 11 }, minWidth: 0 }}>
        {children}
      </Box>
    </Box>
  );
};
