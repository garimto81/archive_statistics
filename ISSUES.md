# GitHub Issues for Archive Statistics

This document contains planned issues to be created on GitHub.

---

## 🐛 Bug Fixes

### Issue #1: Alerts Page Not Implemented
**Labels**: `bug`, `enhancement`
**Priority**: Medium

**Description**:
The Alerts navigation item exists but the page is not implemented.

**Tasks**:
- [ ] Create Alerts page component
- [ ] Add alert threshold settings
- [ ] Implement notification system

---

### Issue #2: Settings Page Not Implemented
**Labels**: `bug`, `enhancement`
**Priority**: Medium

**Description**:
The Settings navigation item exists but the page is not implemented.

**Tasks**:
- [ ] Create Settings page component
- [ ] Add scan configuration options
- [ ] Add NAS connection settings

---

## ✨ Feature Requests

### Issue #3: Add Email Notifications
**Labels**: `enhancement`, `feature`
**Priority**: Medium

**Description**:
Add email notification support for:
- Storage threshold alerts (e.g., 900TB reached)
- Scan completion notifications
- Error alerts

**Acceptance Criteria**:
- [ ] SMTP configuration in settings
- [ ] Email template for notifications
- [ ] Test email functionality

---

### Issue #4: Add Kanban Board View for Work Status
**Labels**: `enhancement`, `feature`
**Priority**: Low

**Description**:
Convert the Work Status table view to include a Kanban board option for better visualization of work progress.

**Tasks**:
- [ ] Implement drag-and-drop columns
- [ ] Status columns: 대기, 작업 중, 완료
- [ ] Filter by Archive/PIC

---

### Issue #5: Scheduled Automatic Scans
**Labels**: `enhancement`, `feature`
**Priority**: Medium

**Description**:
Add ability to schedule automatic scans at specified intervals.

**Tasks**:
- [ ] Add scheduler configuration in Settings
- [ ] Support cron-like scheduling
- [ ] Add scan schedule display in dashboard

---

### Issue #6: File Type Statistics Page Enhancement
**Labels**: `enhancement`
**Priority**: Low

**Description**:
Enhance the Statistics page with:
- Detailed file type breakdown
- Size distribution histogram
- Duration distribution for media files

---

### Issue #7: Dark Mode Support
**Labels**: `enhancement`, `ui`
**Priority**: Low

**Description**:
Add dark mode toggle for better viewing experience.

---

### Issue #8: Export Dashboard as PDF
**Labels**: `enhancement`, `feature`
**Priority**: Low

**Description**:
Allow users to export the current dashboard view as a PDF report.

---

## 🔧 Technical Improvements

### Issue #9: Add Unit Tests
**Labels**: `testing`, `tech-debt`
**Priority**: High

**Description**:
Add comprehensive unit tests for:
- Backend API endpoints
- Scanner service
- Frontend components

---

### Issue #10: Add CI/CD Pipeline
**Labels**: `devops`, `tech-debt`
**Priority**: Medium

**Description**:
Set up GitHub Actions for:
- Automated testing
- Docker image builds
- Deployment automation

---

## 📋 To Create on GitHub

Run these commands (requires `gh` CLI):

```bash
# Install gh CLI first if not installed
# Windows: winget install GitHub.cli

gh auth login

# Create issues
gh issue create --title "Alerts Page Not Implemented" --body "..." --label "bug,enhancement"
gh issue create --title "Settings Page Not Implemented" --body "..." --label "bug,enhancement"
gh issue create --title "Add Email Notifications" --body "..." --label "enhancement,feature"
gh issue create --title "Add Kanban Board View for Work Status" --body "..." --label "enhancement,feature"
gh issue create --title "Scheduled Automatic Scans" --body "..." --label "enhancement,feature"
gh issue create --title "File Type Statistics Page Enhancement" --body "..." --label "enhancement"
gh issue create --title "Dark Mode Support" --body "..." --label "enhancement,ui"
gh issue create --title "Export Dashboard as PDF" --body "..." --label "enhancement,feature"
gh issue create --title "Add Unit Tests" --body "..." --label "testing,tech-debt"
gh issue create --title "Add CI/CD Pipeline" --body "..." --label "devops,tech-debt"
```
