import React, { useEffect, useState, useCallback } from 'react';
import {
  Box, Card, CardContent, Typography, Button, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  IconButton, TextField, Select, MenuItem, FormControl,
  InputLabel, Stack, Pagination, Dialog, DialogTitle,
  DialogContent, DialogActions, CircularProgress, Tooltip, Alert,
} from '@mui/material';
import {
  Add, Send, CheckCircle, Cancel, Publish,
  Flag, Undo, Visibility, Search,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector, useAuth } from '../hooks/useAuth';
import { fetchArticles, transitionArticle, setSelected } from '../store';
import { Article, ArticleStatus } from '../types';
import { STATUS_COLORS } from '../theme';
import { toast } from 'react-toastify';

type TransitionAction = 'submit' | 'approve' | 'reject' | 'publish' | 'dispute' | 'return-to-approver';

interface ActionConfig {
  label: string;
  action: TransitionAction;
  icon: React.ReactNode;
  color: 'primary' | 'success' | 'error' | 'warning' | 'info';
  needsReason?: boolean;
  reasonLabel?: string;
  roles: string[];
  validStatuses: ArticleStatus[];
}

const ACTIONS: ActionConfig[] = [
  { label: 'Submit',     action: 'submit',             icon: <Send />,       color: 'primary',  roles: ['USER'],              validStatuses: ['DRAFT', 'REJECTED'] },
  { label: 'Approve',   action: 'approve',             icon: <CheckCircle />, color: 'success', roles: ['APPROVER', 'ADMIN'], validStatuses: ['PENDING_APPROVAL'] },
  { label: 'Reject',    action: 'reject',              icon: <Cancel />,     color: 'error',    roles: ['APPROVER', 'ADMIN'], needsReason: true, reasonLabel: 'Rejection reason', validStatuses: ['PENDING_APPROVAL'] },
  { label: 'Publish',   action: 'publish',             icon: <Publish />,    color: 'success',  roles: ['PUBLISHER', 'ADMIN'], validStatuses: ['APPROVED'] },
  { label: 'Dispute',   action: 'dispute',             icon: <Flag />,       color: 'warning',  roles: ['PUBLISHER', 'ADMIN'], needsReason: true, reasonLabel: 'Dispute reason',    validStatuses: ['APPROVED'] },
  { label: 'Return',    action: 'return-to-approver',  icon: <Undo />,       color: 'info',     roles: ['PUBLISHER', 'ADMIN'], validStatuses: ['DISPUTED'] },
];

export const ArticlesPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();
  const { items: articles, total, loading } = useAppSelector((s) => s.articles);

  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  const [actionDialog, setActionDialog] = useState<{ open: boolean; article: Article | null; config: ActionConfig | null }>({ open: false, article: null, config: null });
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(() => {
    dispatch(fetchArticles({ page, page_size: 15, status: statusFilter || undefined, search: search || undefined }));
  }, [dispatch, page, statusFilter, search]);

  useEffect(() => { load(); }, [load]);

  const openAction = (article: Article, config: ActionConfig) => {
    setActionDialog({ open: true, article, config });
    setReason('');
  };

  const handleAction = async () => {
    if (!actionDialog.article || !actionDialog.config) return;
    if (actionDialog.config.needsReason && !reason.trim()) {
      toast.error('Please provide a reason');
      return;
    }
    setSubmitting(true);
    try {
      await dispatch(transitionArticle({
        id: actionDialog.article.id,
        action: actionDialog.config.action,
        payload: { reason, comment: reason },
      })).unwrap();
      toast.success(`Article ${actionDialog.config.action}d successfully`);
      setActionDialog({ open: false, article: null, config: null });
      load();
    } catch (e: any) {
      toast.error(e || 'Action failed');
    } finally {
      setSubmitting(false);
    }
  };

  const getAvailableActions = (article: Article): ActionConfig[] => {
    return ACTIONS.filter((a) => {
      const hasRole_ = a.roles.some((r) => hasRole(r as any));
      const validStatus = a.validStatuses.includes(article.status);
      const isAuthor = article.author_id === user?.id;
      if (a.action === 'submit' && !isAuthor) return false;
      return hasRole_ && validStatus;
    });
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h5" fontWeight={700}>Articles</Typography>
          <Typography color="text.secondary" variant="body2">{total} total</Typography>
        </Box>
        {hasRole('USER') && (
          <Button variant="contained" startIcon={<Add />} onClick={() => navigate('/articles/new')}>
            New Article
          </Button>
        )}
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
            <TextField
              placeholder="Search articles..."
              size="small"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              InputProps={{ startAdornment: <Search sx={{ mr: 1, color: 'text.secondary', fontSize: 20 }} /> }}
              sx={{ minWidth: 260 }}
            />
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Status</InputLabel>
              <Select value={statusFilter} label="Status" onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
                <MenuItem value="">All</MenuItem>
                {['DRAFT','PENDING_APPROVAL','APPROVED','REJECTED','DISPUTED','PUBLISHED'].map((s) => (
                  <MenuItem key={s} value={s}>{s.replace('_', ' ')}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Version</TableCell>
                <TableCell>Updated</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}><CircularProgress /></TableCell>
                </TableRow>
              ) : articles.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">No articles found</Typography>
                  </TableCell>
                </TableRow>
              ) : articles.map((article) => {
                const actions = getAvailableActions(article);
                return (
                  <TableRow key={article.id} hover>
                    <TableCell>
                      <Typography fontSize={14} fontWeight={500} sx={{ maxWidth: 300 }} noWrap>
                        {article.title}
                      </Typography>
                      {article.rejection_reason && (
                        <Typography fontSize={11} color="error.main" noWrap>
                          Rejected: {article.rejection_reason}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={article.status.replace('_', ' ')}
                        size="small"
                        color={STATUS_COLORS[article.status] ?? 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography fontSize={13} color="text.secondary">{article.category || '—'}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography fontSize={13} color="text.secondary">v{article.version}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography fontSize={12} color="text.secondary">
                        {new Date(article.updated_at).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View">
                        <IconButton size="small" onClick={() => { dispatch(setSelected(article)); navigate(`/articles/${article.id}`); }}>
                          <Visibility fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {actions.map((cfg) => (
                        <Tooltip key={cfg.action} title={cfg.label}>
                          <IconButton size="small" color={cfg.color} onClick={() => openAction(article, cfg)}>
                            {cfg.icon}
                          </IconButton>
                        </Tooltip>
                      ))}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
        <Box display="flex" justifyContent="center" p={2}>
          <Pagination count={Math.ceil(total / 15)} page={page} onChange={(_, v) => setPage(v)} color="primary" />
        </Box>
      </Card>

      {/* Action Dialog */}
      <Dialog open={actionDialog.open} onClose={() => setActionDialog({ open: false, article: null, config: null })} maxWidth="sm" fullWidth>
        <DialogTitle>{actionDialog.config?.label} Article</DialogTitle>
        <DialogContent>
          <Typography variant="body2" mb={2} color="text.secondary">
            <strong>{actionDialog.article?.title}</strong>
          </Typography>
          {actionDialog.config?.needsReason && (
            <TextField
              label={actionDialog.config.reasonLabel}
              multiline rows={3} fullWidth
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
            />
          )}
          {!actionDialog.config?.needsReason && (
            <TextField
              label="Comment (optional)"
              multiline rows={2} fullWidth
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialog({ open: false, article: null, config: null })}>Cancel</Button>
          <Button
            variant="contained"
            color={actionDialog.config?.color || 'primary'}
            onClick={handleAction}
            disabled={submitting}
          >
            {submitting ? <CircularProgress size={20} /> : `Confirm ${actionDialog.config?.label}`}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
