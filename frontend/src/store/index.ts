import { configureStore, createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api, { tokenStorage } from '../services/api';
import { User, AuthTokens, Article, PaginatedResponse, Notification, PlatformStats } from '../types';

// ─── Auth Slice ───────────────────────────────────────────────────────────────
interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const { data: tokens } = await api.post<AuthTokens>('/auth/login', credentials);
      tokenStorage.set(tokens);
      const { data: user } = await api.get<User>('/auth/me');
      return user;
    } catch (e: any) {
      return rejectWithValue(e.response?.data?.detail || 'Login failed');
    }
  }
);

export const fetchMe = createAsyncThunk('auth/fetchMe', async (_, { rejectWithValue }) => {
  try {
    const { data } = await api.get<User>('/auth/me');
    return data;
  } catch {
    return rejectWithValue('Session expired');
  }
});

export const logout = createAsyncThunk('auth/logout', async () => {
  try { await api.post('/auth/logout'); } catch {}
  tokenStorage.clear();
});

const authSlice = createSlice({
  name: 'auth',
  initialState: { user: null, loading: false, error: null } as AuthState,
  reducers: {
    clearError: (state) => { state.error = null; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (s) => { s.loading = true; s.error = null; })
      .addCase(login.fulfilled, (s, a) => { s.loading = false; s.user = a.payload; })
      .addCase(login.rejected, (s, a) => { s.loading = false; s.error = a.payload as string; })
      .addCase(fetchMe.fulfilled, (s, a) => { s.user = a.payload; })
      .addCase(fetchMe.rejected, (s) => { s.user = null; })
      .addCase(logout.fulfilled, (s) => { s.user = null; });
  },
});

// ─── Articles Slice ───────────────────────────────────────────────────────────
interface ArticlesState {
  items: Article[];
  total: number;
  page: number;
  loading: boolean;
  error: string | null;
  selected: Article | null;
}

export const fetchArticles = createAsyncThunk(
  'articles/fetch',
  async (params: Record<string, unknown> = {}) => {
    const { data } = await api.get<PaginatedResponse<Article>>('/articles', { params });
    return data;
  }
);

export const createArticle = createAsyncThunk(
  'articles/create',
  async (body: Partial<Article>, { rejectWithValue }) => {
    try {
      const { data } = await api.post<Article>('/articles', body);
      return data;
    } catch (e: any) {
      return rejectWithValue(e.response?.data?.detail || 'Failed to create article');
    }
  }
);

export const transitionArticle = createAsyncThunk(
  'articles/transition',
  async ({ id, action, payload }: { id: string; action: string; payload?: object }) => {
    const { data } = await api.post<Article>(`/articles/${id}/${action}`, payload || {});
    return data;
  }
);

const articlesSlice = createSlice({
  name: 'articles',
  initialState: { items: [], total: 0, page: 1, loading: false, error: null, selected: null } as ArticlesState,
  reducers: {
    setSelected: (s, a: PayloadAction<Article | null>) => { s.selected = a.payload; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchArticles.pending, (s) => { s.loading = true; })
      .addCase(fetchArticles.fulfilled, (s, a) => {
        s.loading = false;
        s.items = a.payload.items;
        s.total = a.payload.total;
        s.page = a.payload.page;
      })
      .addCase(fetchArticles.rejected, (s, a) => { s.loading = false; s.error = a.error.message || null; })
      .addCase(createArticle.fulfilled, (s, a) => { s.items.unshift(a.payload); })
      .addCase(transitionArticle.fulfilled, (s, a) => {
        const idx = s.items.findIndex((x) => x.id === a.payload.id);
        if (idx !== -1) s.items[idx] = a.payload;
        if (s.selected?.id === a.payload.id) s.selected = a.payload;
      });
  },
});

// ─── Notifications Slice ──────────────────────────────────────────────────────
interface NotifState { items: Notification[]; unread_count: number; }

export const fetchNotifications = createAsyncThunk('notif/fetch', async () => {
  const { data } = await api.get('/notifications?page_size=10');
  return data;
});

const notifSlice = createSlice({
  name: 'notif',
  initialState: { items: [], unread_count: 0 } as NotifState,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchNotifications.fulfilled, (s, a) => {
      s.items = a.payload.items;
      s.unread_count = a.payload.unread_count;
    });
  },
});

// ─── Store ────────────────────────────────────────────────────────────────────
export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    articles: articlesSlice.reducer,
    notif: notifSlice.reducer,
  },
});

export const { clearError } = authSlice.actions;
export const { setSelected } = articlesSlice.actions;

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
