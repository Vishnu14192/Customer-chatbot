# Chat Hook Refactoring Guide

## Problem

The original `useChat.ts` was 475 lines, making it difficult to:

- Find specific functionality
- Test individual concerns
- Reuse helper functions
- Onboard new developers

## Solution

Split into 5 focused files, each with a single responsibility:

```
hooks/
├── useChat.ts              (80 lines)  - Main orchestrator/composer
├── chatHelpers.ts          (55 lines)  - Pure utility functions
├── useChatState.ts         (70 lines)  - State & derived values
├── useChatActions.ts       (260 lines) - All action functions
└── useChatEffects.ts       (110 lines) - Side effects (bootstrap & lazy-load)
```

**Total: ~575 lines split into 5 files (vs 475 in one file)**

- Each file is now highly focused and testable
- Max file size: 260 lines (still very readable)
- Clear separation of concerns

---

## File Purposes

### 1. **chatHelpers.ts**

**Purpose:** Pure utility functions with no side effects

**Exports:**

- `createId()` - Generate unique IDs
- `createNewThread()` - Create thread objects
- `createMessage()` - Create message objects

**Why separate?**

- Can be tested independently
- Can be used in other modules without importing hook
- Pure functions = easier to reason about

---

### 2. **useChatState.ts**

**Purpose:** State initialization and derived value computation

**Exports:**

- `initializeChatState()` - All useState declarations
- `computeDerivedValues()` - Calculate activeThread, messages, loading, etc.

**Why separate?**

- Centralized state management
- Derived values are explicit and testable
- Easy to see all state in one place
- Can extract state logic for testing without React

---

### 3. **useChatActions.ts**

**Purpose:** All user-facing action functions

**Exports:**

- `createChatActions()` - Factory that returns:
  - `updateThread()` - Immutable thread updates
  - `selectChat()` - Switch active thread
  - `newChat()` - Create new thread
  - `removeChat()` - Delete thread
  - `renameChat()` - Update thread title
  - `send()` - Main chat function with streaming

**Why separate?**

- Actions are the largest/most complex part
- Isolated in own file for easier debugging
- Can be tested with mock state setters
- Clear what modifies state vs. just reads it

---

### 4. **useChatEffects.ts**

**Purpose:** React side effects

**Exports:**

- `useBootstrapEffect()` - Restore threads from backend on mount
- `useLazyLoadEffect()` - Load messages when thread is selected

**Why separate?**

- Effects have complex logic (API calls, dependencies)
- Isolated makes it easier to understand data flow
- Clear which state they depend on
- Can be tested independently

---

### 5. **useChat.ts** (Refactored)

**Purpose:** Main hook that composes everything

**What it does:**

1. Call `initializeChatState()` to setup state
2. Call `computeDerivedValues()` to get derived values
3. Call `createChatActions()` to create actions
4. Setup effects with `useBootstrapEffect()` & `useLazyLoadEffect()`
5. Return unified interface for components

**Why this pattern?**

- Orchestrator pattern keeps main hook readable
- Components only import `useChat`, not internals
- Easy to understand overall flow
- Easy to modify composition without touching details

---

## Usage in Components

**Before (would work the same with refactored code):**

```typescript
const { threads, messages, send, loading, newChat, selectChat } = useChat();
```

**No changes needed in components!** The refactored hook exports the same interface.

---

## Migration Steps

1. **Create new files:**
   - `chatHelpers.ts`
   - `useChatState.ts`
   - `useChatActions.ts`
   - `useChatEffects.ts`

2. **Update `useChat.ts`** to use new imports

3. **Test:**
   - Frontend lint: `npm run lint`
   - Components still work as before
   - No API changes

4. **Delete old `useChat.ts` backup** (keep refactored version)

---

## Benefits of This Structure

| Before                             | After                        |
| ---------------------------------- | ---------------------------- |
| 1 file (475 lines)                 | 5 files (avg 115 lines)      |
| Mixed concerns                     | Single responsibility        |
| Hard to test                       | Easy to unit test each part  |
| Hard to navigate                   | Clear module boundaries      |
| Reuse helpers? Have to import hook | Import just `chatHelpers.ts` |

---

## Development Tips

### Adding a new action?

→ Add to `useChatActions.ts`

### Need a new state value?

→ Add to `useChatState.ts`

### Need to change bootstrap logic?

→ Edit `useBootstrapEffect` in `useChatEffects.ts`

### Need new utility?

→ Add to `chatHelpers.ts`

### Need to change what hook exports?

→ Edit main `useChat.ts` return statement

---

## Testing Strategy

Each file can be tested independently:

```typescript
// Test helpers
test("createId returns unique strings", () => {
  const id1 = createId();
  const id2 = createId();
  expect(id1).not.toBe(id2);
});

// Test state
test("computeDerivedValues finds active thread", () => {
  const values = computeDerivedValues(threads, activeId, null, false);
  expect(values.activeThread.id).toBe(activeId);
});

// Test actions with mock setters
test("newChat creates thread with correct title", () => {
  const setThreads = jest.fn();
  const actions = createChatActions([], setThreads, "", jest.fn(), jest.fn());
  actions.newChat();
  expect(setThreads).toHaveBeenCalled();
});
```

---

## Summary

✅ Code is now modular and maintainable  
✅ Each file has a single, clear purpose  
✅ Easier to find and modify functionality  
✅ Better for testing and onboarding  
✅ Components see no breaking changes
