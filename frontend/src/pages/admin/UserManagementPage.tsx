import React, { useEffect, useState, useCallback } from 'react';
import {
  Box, Card, CardContent, Typography, Button, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, IconButton, Avatar, Dialog, DialogTitle, DialogContent,
  DialogActions, FormControl, InputLabel, Select, MenuItem,
  OutlinedInput, Checkbox, ListItemText, Pagination, Tooltip,
  Stack, CircularProgress, Alert, Switch, FormControlLabel,
} from '@mui/material';
import {
  Add, Edit, Delete, AdminPanelSettings,
  Search, Refresh, PersonOff, PersonAdd,
} from '@mui/icons-material';
import api from '../../services/api';
import { User, PaginatedResponse, RoleName } from '../../types';
import { ROLE_COLORS } from '../../theme';
import { toast } from 'react-toastify';

const ROLES: RoleName[] = ['ADMIN', 'USER', 'APPROVER', 'PUBLISHER'];

interface CreateUserForm {
  email: string;
  username: string;
  full_name: string;
  password: string;
  department: string;
  role_names: RoleName[];
}

const defaultForm: CreateUserForm = {
  email: '', username: '', full_name: '', password: '',
  department: '', role_names: ['USER'],
};

export const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [createOpen, setCreateOpen] = useState(false);
  const [rolesOpen, setRolesOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [form, setForm] = useState<CreateUserForm>(defaultForm);
  const [newRoles, setNewRoles] = useState<RoleName[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get<PaginatedResponse<User>>('/users', {
        params: { page, page_size: 15, search: search || undefined },
      });
      setUsers(data.items);
      setTotal(data.total);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const handleCreate = async () => {
    setSubmitting(true);
    try {
      await api.post('/users', form);
      toast.success('User created successfully');
      setCreateOpen(false);
      setForm(defaultForm);
      fetchUsers();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to create user');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (user: User) => {
    try {
      await api.post(`/users/${user.id}/toggle-active`);
      toast.success(`User ${user.is_active ? 'deactivated' : 'activated'}`);
      fetchUsers();
    } catch {
      toast.error('Failed to update user status');
    }
  };

  const handleAssignRoles = async () => {
    if (!selectedUser) return;
    setSubmitting(true);
    try {
      await api.put(`/users/${selectedUser.id}/roles`, { role_names: newRoles });
      toast.success('Roles updated successfully');
      setRolesOpen(false);
      fetchUsers();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to update roles');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (user: User) => {
    if (!window.confirm(`Delete user ${user.full_name}? This cannot be undone.`)) return;
    try {
      await api.delete(`/users/${user.id}`);
      toast.success('User deleted');
      fetchUsers();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to delete user');
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h5" fontWeight={700}>User Management</Typography>
          <Typography color="text.secondary" variant="body2">{total} total users</Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setCreateOpen(true)}>
          Create User
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Search */}
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <TextField
              placeholder="Search by name or email..."
              size="small"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              InputProps={{ startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} /> }}
              sx={{ flex: 1, maxWidth: 400 }}
            />
            <IconButton onClick={fetchUsers}><Refresh /></IconButton>
          </Stack>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>User</TableCell>
                <TableCell>Roles</TableCell>
                <TableCell>Department</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Joined</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <CircularProgress size={32} />
                  </TableCell>
                </TableRow>
              ) : users.map((user) => (
                <TableRow key={user.id} hover>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1.5}>
                      <Avatar sx={{ bgcolor: 'primary.main', width: 36, height: 36, fontSize: 14 }}>
                        {user.full_name[0].toUpperCase()}
                      </Avatar>
                      <Box>
                        <Typography fontSize={14} fontWeight={500}>{user.full_name}</Typography>
                        <Typography fontSize={12} color="text.secondary">{user.email}</Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {user.roles.map((r) => (
                        <Chip
                          key={r}
                          label={r}
                          size="small"
                          sx={{ bgcolor: ROLE_COLORS[r] + '22', color: ROLE_COLORS[r], fontWeight: 700, fontSize: 10 }}
                        />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography fontSize={13} color="text.secondary">{user.department || '—'}</Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.is_active ? 'Active' : 'Inactive'}
                      color={user.is_active ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography fontSize={12} color="text.secondary">
                      {new Date(user.created_at).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Assign Roles">
                      <IconButton
                        size="small"
                        onClick={() => { setSelectedUser(user); setNewRoles(user.roles); setRolesOpen(true); }}
                      >
                        <AdminPanelSettings fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={user.is_active ? 'Deactivate' : 'Activate'}>
                      <IconButton size="small" onClick={() => handleToggleActive(user)}>
                        {user.is_active ? <PersonOff fontSize="small" /> : <PersonAdd fontSize="small" />}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" color="error" onClick={() => handleDelete(user)}>
                        <Delete fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <Box display="flex" justifyContent="center" p={2}>
          <Pagination
            count={Math.ceil(total / 15)}
            page={page}
            onChange={(_, v) => setPage(v)}
            color="primary"
          />
        </Box>
      </Card>

      {/* Create User Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New User</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField label="Full Name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} fullWidth required />
            <TextField label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} fullWidth required />
            <TextField label="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} fullWidth required />
            <TextField label="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} fullWidth required helperText="Min 8 chars, 1 uppercase, 1 number" />
            <TextField label="Department" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} fullWidth />
            <FormControl fullWidth>
              <InputLabel>Roles</InputLabel>
              <Select
                multiple value={form.role_names}
                onChange={(e) => setForm({ ...form, role_names: e.target.value as RoleName[] })}
                input={<OutlinedInput label="Roles" />}
                renderValue={(selected) => selected.join(', ')}
              >
                {ROLES.map((r) => (
                  <MenuItem key={r} value={r}>
                    <Checkbox checked={form.role_names.includes(r)} />
                    <ListItemText primary={r} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={submitting}>
            {submitting ? <CircularProgress size={20} /> : 'Create User'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Assign Roles Dialog */}
      <Dialog open={rolesOpen} onClose={() => setRolesOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Assign Roles — {selectedUser?.full_name}</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel>Roles</InputLabel>
            <Select
              multiple value={newRoles}
              onChange={(e) => setNewRoles(e.target.value as RoleName[])}
              input={<OutlinedInput label="Roles" />}
              renderValue={(selected) => selected.join(', ')}
            >
              {ROLES.map((r) => (
                <MenuItem key={r} value={r}>
                  <Checkbox checked={newRoles.includes(r)} />
                  <ListItemText primary={r} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRolesOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAssignRoles} disabled={submitting}>
            {submitting ? <CircularProgress size={20} /> : 'Save Roles'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
