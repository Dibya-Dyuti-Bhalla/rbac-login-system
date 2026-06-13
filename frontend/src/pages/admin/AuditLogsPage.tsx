import React, { useEffect, useState } from 'react';
import {
  Box, Card, CardContent, Typography, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Chip,
  TextField, Stack, Pagination, CircularProgress,
  Accordion, AccordionSummary, AccordionDetails,
} from '@mui/material';
import { ExpandMore, History } from '@mui/icons-material';
import api from '../../services/api';
import { AuditLogEntry } from '../../types';

const ACTION_COLOR: Record<string, 'success' | 'error' | 'warning' | 'info' | 'default'> = {
  'auth.login': 'info',
  'auth.logout': 'default',
  'user.created': 'success',
  'user.deleted': 'error',
  'user.roles_assigned': 'warning',
  'user.activated': 'success',
  'user.deactivated': 'error',
  'article.created': 'info',
  'article.updated': 'default',
  'article.pending_approval': 'warning',
  'article.approved': 'success',
  'article.rejected': 'error',
  'article.published': 'success',
  'article.disputed': 'warning',
};

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/admin/audit-logs', {
        params: {
          page, page_size: 25,
          action: actionFilter || undefined,
          resource_type: resourceFilter || undefined,
        },
      });
      setLogs(data.items);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLogs(); }, [page, actionFilter, resourceFilter]);

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={1} mb={3}>
        <History color="primary" />
        <Box>
          <Typography variant="h5" fontWeight={700}>Audit Logs</Typography>
          <Typography color="text.secondary" variant="body2">{total} total entries</Typography>
        </Box>
      </Box>

      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Stack direction="row" spacing={2}>
            <TextField
              label="Filter by action"
              size="small"
              value={actionFilter}
              onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
              placeholder="e.g. article.approved"
              sx={{ minWidth: 200 }}
            />
            <TextField
              label="Resource type"
              size="small"
              value={resourceFilter}
              onChange={(e) => { setResourceFilter(e.target.value); setPage(1); }}
              placeholder="user / article"
              sx={{ minWidth: 160 }}
            />
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>Action</TableCell>
                <TableCell>Resource</TableCell>
                <TableCell>Actor</TableCell>
                <TableCell>IP</TableCell>
                <TableCell>Changes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}><CircularProgress size={28} /></TableCell>
                </TableRow>
              ) : logs.map((log) => (
                <TableRow key={log.id} hover>
                  <TableCell>
                    <Typography fontSize={12} color="text.secondary">
                      {new Date(log.created_at).toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={log.action}
                      size="small"
                      color={ACTION_COLOR[log.action] ?? 'default'}
                      sx={{ fontFamily: 'monospace', fontSize: 11 }}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography fontSize={12}>{log.resource_type}</Typography>
                    {log.resource_id && (
                      <Typography fontSize={10} color="text.secondary" fontFamily="monospace">
                        {log.resource_id.slice(0, 8)}...
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography fontSize={12} fontFamily="monospace" color="text.secondary">
                      {log.actor_id ? log.actor_id.slice(0, 8) + '...' : 'system'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography fontSize={12} color="text.secondary">{log.ip_address || '—'}</Typography>
                  </TableCell>
                  <TableCell>
                    {(log.old_values || log.new_values) && (
                      <Accordion disableGutters elevation={0} sx={{ bgcolor: 'transparent', border: 'none' }}>
                        <AccordionSummary expandIcon={<ExpandMore sx={{ fontSize: 16 }} />} sx={{ p: 0, minHeight: 0, '& .MuiAccordionSummary-content': { m: 0 } }}>
                          <Typography fontSize={11} color="primary.main">View diff</Typography>
                        </AccordionSummary>
                        <AccordionDetails sx={{ p: 0, pt: 1 }}>
                          {log.old_values && (
                            <Box mb={0.5}>
                              <Typography fontSize={10} color="error.main" fontWeight={600}>Before:</Typography>
                              <Typography fontSize={10} fontFamily="monospace" color="text.secondary" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                                {JSON.stringify(log.old_values, null, 2)}
                              </Typography>
                            </Box>
                          )}
                          {log.new_values && (
                            <Box>
                              <Typography fontSize={10} color="success.main" fontWeight={600}>After:</Typography>
                              <Typography fontSize={10} fontFamily="monospace" color="text.secondary" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                                {JSON.stringify(log.new_values, null, 2)}
                              </Typography>
                            </Box>
                          )}
                        </AccordionDetails>
                      </Accordion>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <Box display="flex" justifyContent="center" p={2}>
          <Pagination count={Math.ceil(total / 25)} page={page} onChange={(_, v) => setPage(v)} color="primary" />
        </Box>
      </Card>
    </Box>
  );
};
