import { configureStore } from '@reduxjs/toolkit'
import authReducer from './authSlice'
import nonprofitReducer from './nonprofitSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    nonprofit: nonprofitReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
