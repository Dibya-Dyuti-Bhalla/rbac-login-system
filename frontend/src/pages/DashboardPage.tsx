import React, { useEffect, useState } from 'react';
import {
  Grid, Card, CardContent, Typography, Box, Chip,
  LinearProgress, Avatar, List, ListItem, ListItemAvatar,
  ListItemText, Skeleton,
} from '@mui/material';
import {
  People, Article, CheckCircle, Pending,
  TrendingUp, Block, Publish,
} from '@mui/icons-material';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { PlatformStats, Article as ArticleType } from '../types';
import { STATUS_COLORS } from '../theme';

const STATUS_CHART_COLORS: Record<string, string> = {
  DRAFT: '#64748b',
  PENDING_APPROVAL: '#f59e0b',
  APPROVED: '#22c55e',
  REJECTED: '#ef4444',
  DISPUTED: '#3b82f6',
  PUBLISHED: '#a78bfa',
};

const StatCard: React.FC<{ label: string; value: number | string; icon: React.ReactNode; color: string }> = ({
  label, value, icon, color,
}) => (
  <Card>
    <CardContent>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>{label}</Typography>
          <Typography variant="h4" fontWeight={700}>{value}</Typography>
        </Box>
        <Avatar sx={{ bgcolor: color + '22', color, width: 48, height: 48 }}>{icon}</Avatar>
      </Box>
    </CardContent>
  </Card>
);

export const DashboardPage: React.FC = () => {
  const { user, isAdmin, isApprover, isPublisher } = useAuth();
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [recentArticles, setRecentArticles] = useState<ArticleType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [articlesRes] = await Promise.all([
          api.get('/articles?page_size=5'),
        ]);
        setRecentArticles(articlesRes.data.items);

        if (isAdmin) {
          const statsRes = await api.get('/admin/stats');
          setStats(statsRes.data);
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [isAdmin]);

  if (loading) return <LinearProgress />;

  const pieData = stats
    ? Object.entries(stats.articles.by_status).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} mb={0.5}>
        Welcome back, {user?.full_name?.split(' ')[0]} 👋
      </Typography>
      <Typography color="text.secondary" mb={3}>
        Here's what's happening on the platform today.
      </Typography>

      {/* Admin stats */}
      {isAdmin && stats && (
        <>
          <Grid container spacing={2} mb={3}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard label="Total Users" value={stats.users.total} icon={<People />} color="#6366f1" />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard label="Active Users" value={stats.users.active} icon={<CheckCircle />} color="#22c55e" />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard label="Total Articles" value={stats.articles.total} icon={<Article />} color="#f59e0b" />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                label="Pending Approval"
                value={stats.articles.by_status['PENDING_APPROVAL'] ?? 0}
                icon={<Pending />}
                color="#ef4444"
              />
            </Grid>
          </Grid>

          <Grid container spacing={3} mb={3}>
            <Grid item xs={12} md={7}>
              <Card>
                <CardContent>
                  <Typography variant="h6" mb={2}>Articles by Status</Typography>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={Object.entries(stats.articles.by_status).map(([name, value]) => ({ name, value }))}>
                      <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <ReTooltip />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {Object.keys(stats.articles.by_status).map((status) => (
                          <Cell key={status} fill={STATUS_CHART_COLORS[status] || '#6366f1'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={5}>
              <Card>
                <CardContent>
                  <Typography variant="h6" mb={2}>Distribution</Typography>
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                        {pieData.map((entry) => (
                          <Cell key={entry.name} fill={STATUS_CHART_COLORS[entry.name] || '#6366f1'} />
                        ))}
                      </Pie>
                      <ReTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}

      {/* Recent articles */}
      <Card>
        <CardContent>
          <Typography variant="h6" mb={2}>
            {isAdmin ? 'Recent Articles (All)' : isApprover ? 'Pending Reviews' : isPublisher ? 'Publish Queue' : 'My Articles'}
          </Typography>
          {recentArticles.length === 0 ? (
            <Typography color="text.secondary" textAlign="center" py={4}>No articles yet</Typography>
          ) : (
            <List disablePadding>
              {recentArticles.map((article, i) => (
                <ListItem
                  key={article.id}
                  divider={i < recentArticles.length - 1}
                  sx={{ px: 0 }}
                >
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'primary.main', width: 36, height: 36, fontSize: 14 }}>
                      {article.title[0].toUpperCase()}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={article.title}
                    secondary={`v${article.version} · ${new Date(article.updated_at).toLocaleDateString()}`}
                    primaryTypographyProps={{ fontWeight: 500, fontSize: 14 }}
                    secondaryTypographyProps={{ fontSize: 12 }}
                  />
                  <Chip
                    label={article.status.replace('_', ' ')}
                    size="small"
                    color={STATUS_COLORS[article.status] ?? 'default'}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};
