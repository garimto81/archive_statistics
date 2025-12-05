# Archive Statistics Dashboard - UI Mockup

## 1. 전체 화면 레이아웃

```mermaid
block-beta
    columns 12

    block:header:12
        columns 12
        logo["GGP Archive Statistics"]:4
        space:4
        scanBtn["Scan Now"]:2
        settingsBtn["Settings"]:2
    end

    space:12

    block:stats:12
        columns 4
        card1["Total Files\n1,234,567"]:1
        card2["Total Size\n856.3 TB"]:1
        card3["Duration\n45,230 hrs"]:1
        card4["File Types\n32"]:1
    end

    space:12

    block:main:12
        columns 12
        tree["Folder Tree"]:4
        charts["Charts Area"]:8
    end

    space:12

    block:footer:12
        columns 12
        status["Last Scan: 2025-12-05 14:30:00 | Status: Online"]:12
    end
```

---

## 2. 메인 대시보드 상세

```mermaid
flowchart TB
    subgraph Page["Archive Statistics Dashboard"]
        direction TB

        subgraph Header["Header Bar"]
            direction LR
            Logo["GGP Archive<br/>Statistics"]
            NavHome["Dashboard"]
            NavTree["Folder View"]
            NavStats["Statistics"]
            NavHistory["History"]
            NavAlerts["Alerts"]
            NavSettings["Settings"]
            ScanButton["Scan Now"]
        end

        subgraph StatsRow["Statistics Summary"]
            direction LR

            subgraph Card1["Total Files"]
                Icon1["Files Icon"]
                Value1["1,234,567"]
                Change1["+2,340 today"]
            end

            subgraph Card2["Total Size"]
                Icon2["Storage Icon"]
                Value2["856.3 TB"]
                Change2["+1.2 TB today"]
            end

            subgraph Card3["Media Duration"]
                Icon3["Clock Icon"]
                Value3["45,230 hrs"]
                Change3["+120 hrs today"]
            end

            subgraph Card4["File Types"]
                Icon4["Type Icon"]
                Value4["32 types"]
                Change4["MP4 is largest"]
            end
        end

        subgraph MainArea["Main Content Area"]
            direction LR

            subgraph LeftPanel["Folder Tree Panel - 33%"]
                direction TB
                SearchBox["Search folders..."]
                TreeRoot["ARCHIVE"]
                Tree2024["2024 - 450 TB"]
                Tree2025["2025 - 320 TB"]
                TreeLegacy["Legacy - 86 TB"]
            end

            subgraph RightPanel["Charts Panel - 67%"]
                direction TB

                subgraph ChartRow1["Top Charts"]
                    direction LR
                    PieChart["File Type Distribution<br/>Pie Chart"]
                    BarChart["Top 10 Folders<br/>Bar Chart"]
                end

                subgraph ChartRow2["Bottom Chart"]
                    LineChart["Storage Growth Trend<br/>Line Chart - 12 months"]
                end
            end
        end

        subgraph Footer["Status Bar"]
            LastScan["Last Scan: 2025-12-05 14:30:00"]
            ServerStatus["Server: Online"]
            NASStatus["NAS: Connected"]
        end
    end

    Header --> StatsRow
    StatsRow --> MainArea
    MainArea --> Footer
```

---

## 3. 폴더 트리 뷰 (상세)

```mermaid
flowchart TD
    subgraph FolderExplorer["Folder Explorer View"]
        direction TB

        subgraph Toolbar["Toolbar"]
            direction LR
            BtnExpand["Expand All"]
            BtnCollapse["Collapse All"]
            BtnRefresh["Refresh"]
            SearchInput["Search: "]
            SortSelect["Sort by: Size"]
        end

        subgraph TreeView["Interactive Folder Tree"]
            direction TB

            Root["ARCHIVE<br/>856.3 TB | 1.2M files"]

            Root --> F2024["2024<br/>450 TB | 623K files"]
            Root --> F2025["2025<br/>320 TB | 512K files"]
            Root --> FLegacy["Legacy<br/>86.3 TB | 89K files"]

            F2024 --> F2024_Proj["Projects<br/>280 TB"]
            F2024 --> F2024_Back["Backups<br/>120 TB"]
            F2024 --> F2024_Media["Media<br/>50 TB"]

            F2024_Proj --> ProjA["ProjectA<br/>80 TB"]
            F2024_Proj --> ProjB["ProjectB<br/>120 TB"]
            F2024_Proj --> ProjC["ProjectC<br/>80 TB"]

            F2025 --> F2025_Q1["Q1<br/>80 TB"]
            F2025 --> F2025_Q2["Q2<br/>85 TB"]
            F2025 --> F2025_Q3["Q3<br/>90 TB"]
            F2025 --> F2025_Q4["Q4<br/>65 TB"]
        end

        subgraph Details["Selected Folder Details"]
            direction LR
            DetailPath["Path: /ARCHIVE/2024/Projects"]
            DetailSize["Size: 280 TB"]
            DetailFiles["Files: 234,567"]
            DetailFolders["Subfolders: 156"]
        end
    end

    Toolbar --> TreeView
    TreeView --> Details
```

---

## 4. 통계 차트 영역

### 4.1 파일 형식별 분포 (Pie Chart)

```mermaid
pie showData
    title File Type Distribution
    "Video (MP4, MKV, AVI)" : 45.2
    "Image (JPG, PNG, RAW)" : 25.8
    "Audio (MP3, WAV, FLAC)" : 15.3
    "Document (PDF, DOC)" : 8.5
    "Other" : 5.2
```

### 4.2 월별 용량 추이 (Line Chart)

```mermaid
xychart-beta
    title "Monthly Storage Growth (TB)"
    x-axis ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    y-axis "Storage (TB)" 700 --> 900
    line "Total" [720, 735, 752, 770, 788, 805, 820, 835, 845, 852, 855, 856]
    line "Video" [350, 360, 370, 382, 395, 408, 420, 430, 438, 445, 448, 450]
```

### 4.3 폴더별 용량 Top 10 (Bar Chart - 개념)

```mermaid
xychart-beta
    title "Top 10 Folders by Size (TB)"
    x-axis ["2024/Projects", "2025/Q3", "2024/Backups", "2025/Q2", "2025/Q1", "Legacy/Old", "2024/Media", "2025/Q4", "Legacy/Archive", "2024/Temp"]
    y-axis "Size (TB)" 0 --> 300
    bar [280, 90, 120, 85, 80, 50, 50, 65, 36, 25]
```

---

## 5. 폴더 트리맵 시각화

```mermaid
flowchart TB
    subgraph Treemap["Folder Treemap - Click to Drill Down"]
        direction TB

        subgraph Level1["ARCHIVE (856 TB)"]
            direction LR

            subgraph Box2024["2024"]
                direction TB
                L2024["450 TB<br/>52.5%"]
                style L2024 fill:#4CAF50
            end

            subgraph Box2025["2025"]
                direction TB
                L2025["320 TB<br/>37.4%"]
                style L2025 fill:#2196F3
            end

            subgraph BoxLegacy["Legacy"]
                direction TB
                LLegacy["86 TB<br/>10.1%"]
                style LLegacy fill:#FF9800
            end
        end

        subgraph Level2["2024 Expanded"]
            direction LR

            subgraph BoxProj["Projects"]
                LProj["280 TB<br/>62.2%"]
                style LProj fill:#66BB6A
            end

            subgraph BoxBack["Backups"]
                LBack["120 TB<br/>26.7%"]
                style LBack fill:#81C784
            end

            subgraph BoxMedia["Media"]
                LMedia["50 TB<br/>11.1%"]
                style LMedia fill:#A5D6A7
            end
        end
    end

    Level1 --> Level2
```

---

## 6. 알림 설정 페이지

```mermaid
flowchart TB
    subgraph AlertSettings["Alert Configuration"]
        direction TB

        subgraph AlertList["Active Alerts"]
            direction TB
            Alert1["Storage Warning<br/>Trigger: 900 TB<br/>Status: Active"]
            Alert2["Daily Growth<br/>Trigger: > 5 TB/day<br/>Status: Active"]
            Alert3["File Count<br/>Trigger: > 2M files<br/>Status: Inactive"]
        end

        subgraph NewAlert["Create New Alert"]
            direction LR
            InputName["Alert Name: "]
            InputType["Type: Storage / Growth / Files"]
            InputThreshold["Threshold: "]
            InputEmail["Email: "]
            BtnCreate["Create Alert"]
        end

        subgraph NotifySettings["Notification Settings"]
            direction LR
            OptEmail["Email Notifications: ON"]
            OptWeb["Web Notifications: ON"]
            OptSlack["Slack Integration: OFF"]
        end
    end

    AlertList --> NewAlert
    NewAlert --> NotifySettings
```

---

## 7. 스캔 진행 모달

```mermaid
flowchart TB
    subgraph ScanModal["Scan Progress"]
        direction TB

        subgraph Progress["Scanning Archive..."]
            ProgressBar["=========>          60%"]
            CurrentFolder["Current: /ARCHIVE/2024/Projects/ProjectB"]
            FilesScanned["Files Scanned: 742,340 / 1,234,567"]
            TimeElapsed["Time Elapsed: 00:15:32"]
            TimeRemaining["Estimated Remaining: 00:10:21"]
        end

        subgraph Stats["Scan Statistics"]
            NewFiles["New Files Found: 2,340"]
            DeletedFiles["Deleted Files: 156"]
            SizeChange["Size Change: +1.2 TB"]
        end

        subgraph Actions["Actions"]
            BtnPause["Pause"]
            BtnCancel["Cancel"]
        end
    end

    Progress --> Stats
    Stats --> Actions
```

---

## 8. 히스토리 페이지

```mermaid
flowchart TB
    subgraph HistoryPage["Storage History"]
        direction TB

        subgraph Filters["Date Range Filter"]
            direction LR
            DateFrom["From: 2025-01-01"]
            DateTo["To: 2025-12-05"]
            BtnApply["Apply"]
            BtnExport["Export CSV"]
        end

        subgraph Chart["Historical Trend"]
            TrendChart["Storage Growth Chart<br/>━━━━━━━━━━━━━━━━━━━━━<br/>856 TB ┤        ___/'''<br/>800 TB ┤    ___/<br/>750 TB ┤___/<br/>700 TB ┼───────────────────<br/>        Jan  Mar  May  Jul  Sep  Nov"]
        end

        subgraph Table["History Table"]
            Header["Date | Total Size | Files | Change"]
            Row1["2025-12-05 | 856.3 TB | 1,234,567 | +1.2 TB"]
            Row2["2025-12-04 | 855.1 TB | 1,232,227 | +0.8 TB"]
            Row3["2025-12-03 | 854.3 TB | 1,230,890 | +1.5 TB"]
            Row4["2025-12-02 | 852.8 TB | 1,228,450 | +0.9 TB"]
            Row5["... | ... | ... | ..."]
        end
    end

    Filters --> Chart
    Chart --> Table
```

---

## 9. 아카이빙 작업 현황 관리 페이지 (Work Status Tracker)

### 9.1 작업 현황 대시보드

```mermaid
flowchart TB
    subgraph WorkStatusPage["Archiving Work Status Dashboard"]
        direction TB

        subgraph Header["Header"]
            direction LR
            Title["Archiving Work Status"]
            BtnImport["Import CSV"]
            BtnExport["Export Excel"]
            BtnAdd["+ Add Task"]
        end

        subgraph Summary["Progress Summary Cards"]
            direction LR

            subgraph SumTotal["Total Tasks"]
                TotalVal["10"]
                TotalLabel["Archives"]
            end

            subgraph SumProgress["In Progress"]
                ProgressVal["3"]
                ProgressLabel["Active"]
            end

            subgraph SumComplete["Completed"]
                CompleteVal["45%"]
                CompleteLabel["Overall"]
            end

            subgraph SumVideos["Total Videos"]
                VideosVal["1,669"]
                VideosLabel["Files"]
            end
        end

        subgraph MainTable["Work Status Table"]
            direction TB
            TableHeader["Archive | Category | PIC | Status | Total | Done | Progress | Notes"]
            Row1["WSOP | WSOP Paradise | Richie, Hunter | 작업 중 | 26 | 0 | 0% | WSOP Paradise, LA 작업 중"]
            Row2["WSOP | WSOP Europe | - | 대기 | 65 | 0 | 0% | -"]
            Row3["WSOP | WSOP LA | - | 대기 | 11 | 0 | 0% | -"]
            Row4["WSOP | PAD | - | 대기 | 44 | 0 | 0% | -"]
            Row5["HCL | Clip 2023 | Zed, Mike | 작업 중 | 500 | 0 | 0% | 년도별 다운로드 진행 중"]
            Row6["HCL | Clip 2024 | - | 대기 | 500 | 0 | 0% | -"]
            Row7["HCL | Clip 2025 | - | 대기 | 500 | 0 | 0% | -"]
        end
    end

    Header --> Summary
    Summary --> MainTable
```

### 9.2 아카이브별 진행률 차트

```mermaid
pie showData
    title Archive Progress by Category
    "WSOP (169 videos)" : 169
    "HCL (1500 videos)" : 1500
```

### 9.3 담당자(PIC)별 작업 현황

```mermaid
xychart-beta
    title "Work Status by PIC"
    x-axis ["Richie/Hunter", "Zed/Mike", "Unassigned"]
    y-axis "Number of Videos" 0 --> 1600
    bar "Total" [26, 500, 1143]
    bar "Done" [0, 0, 0]
```

### 9.4 칸반 보드 스타일 뷰

```mermaid
flowchart LR
    subgraph Kanban["Work Status Kanban Board"]
        direction LR

        subgraph Backlog["📋 Backlog"]
            direction TB
            B1["WSOP Europe<br/>65 videos"]
            B2["WSOP 2022-2025<br/>TBD"]
            B3["PAD<br/>44 videos"]
            B4["GOG<br/>12 videos"]
            B5["MPP<br/>11 videos"]
        end

        subgraph InProgress["🔄 In Progress"]
            direction TB
            P1["WSOP Paradise<br/>Richie, Hunter<br/>26 videos<br/>0%"]
            P2["HCL Clip 2023<br/>Zed, Mike<br/>500 videos<br/>0%"]
        end

        subgraph Review["👀 Review"]
            direction TB
            R1["(No items)"]
        end

        subgraph Done["✅ Done"]
            direction TB
            D1["(No items)"]
        end
    end

    Backlog --> InProgress
    InProgress --> Review
    Review --> Done
```

### 9.5 작업 상세 편집 모달

```mermaid
flowchart TB
    subgraph EditModal["Edit Task Modal"]
        direction TB

        subgraph Form["Task Details"]
            direction TB
            F1["Archive: [WSOP ▼]"]
            F2["Category: [WSOP Paradise]"]
            F3["PIC: [Richie, Hunter]"]
            F4["Status: [작업 중 ▼]"]
            F5["Total Videos: [26]"]
            F6["Excel Done: [0]"]
            F7["Progress: [0%] (자동계산)"]
            F8["Notes: [WSOP Paradise, LA 작업 중]"]
        end

        subgraph Actions["Actions"]
            direction LR
            BtnSave["💾 Save"]
            BtnCancel["❌ Cancel"]
            BtnDelete["🗑️ Delete"]
        end
    end

    Form --> Actions
```

### 9.6 CSV Import 화면

```mermaid
flowchart TB
    subgraph ImportModal["CSV Import"]
        direction TB

        subgraph Upload["File Upload"]
            DropZone["📁 Drag & Drop CSV file here<br/>or click to browse"]
        end

        subgraph Preview["Data Preview"]
            PreviewTable["Archive | Category | PIC | Status | Total | Done<br/>WSOP | WSOP Paradise | Richie | 작업 중 | 26 | 0<br/>WSOP | WSOP Europe | - | 대기 | 65 | 0<br/>..."]
        end

        subgraph Options["Import Options"]
            Opt1["☑ Replace existing data"]
            Opt2["☐ Append to existing"]
            Opt3["☑ Skip header row"]
        end

        subgraph ImportActions["Actions"]
            BtnImportConfirm["✅ Import"]
            BtnImportCancel["❌ Cancel"]
        end
    end

    Upload --> Preview
    Preview --> Options
    Options --> ImportActions
```

---

## 10. 반응형 레이아웃

### 10.1 Desktop (1920px+)

```mermaid
block-beta
    columns 12

    Header["Header"]:12
    Stats1:3
    Stats2:3
    Stats3:3
    Stats4:3
    FolderTree["Folder Tree"]:4
    Charts["Charts"]:8
    Footer["Footer"]:12
```

### 10.2 Tablet (768px - 1024px)

```mermaid
block-beta
    columns 6

    Header["Header"]:6
    Stats1:3
    Stats2:3
    Stats3:3
    Stats4:3
    FolderTree["Folder Tree"]:6
    Charts["Charts"]:6
    Footer["Footer"]:6
```

### 10.3 Mobile (< 768px)

```mermaid
block-beta
    columns 1

    Header["Header"]
    Stats1["Stats Card 1"]
    Stats2["Stats Card 2"]
    Stats3["Stats Card 3"]
    Stats4["Stats Card 4"]
    FolderTree["Folder Tree (Collapsed)"]
    Charts["Charts (Stacked)"]
    Footer["Footer"]
```

---

## 11. 컬러 스키마

```mermaid
flowchart LR
    subgraph Colors["Color Palette"]
        direction TB

        subgraph Primary["Primary Colors"]
            P1["#1976D2 - Primary Blue"]
            P2["#1565C0 - Dark Blue"]
            P3["#42A5F5 - Light Blue"]
        end

        subgraph Secondary["Secondary Colors"]
            S1["#4CAF50 - Success Green"]
            S2["#FF9800 - Warning Orange"]
            S3["#F44336 - Error Red"]
        end

        subgraph Neutral["Neutral Colors"]
            N1["#FFFFFF - Background"]
            N2["#F5F5F5 - Card BG"]
            N3["#212121 - Text"]
            N4["#757575 - Secondary Text"]
        end

        subgraph FileTypes["File Type Colors"]
            F1["#E91E63 - Video"]
            F2["#9C27B0 - Image"]
            F3["#00BCD4 - Audio"]
            F4["#795548 - Document"]
        end
    end
```

---

## 12. 사용자 흐름 (User Flow)

```mermaid
flowchart TD
    Start["User Opens App"] --> Dashboard["View Dashboard"]

    Dashboard --> ViewStats["View Statistics Cards"]
    Dashboard --> ViewTree["Explore Folder Tree"]
    Dashboard --> ViewCharts["Analyze Charts"]
    Dashboard --> StartScan["Start Manual Scan"]

    ViewTree --> SelectFolder["Select Folder"]
    SelectFolder --> FolderDetails["View Folder Details"]
    FolderDetails --> DrillDown["Drill Down Subfolders"]

    ViewCharts --> FilterData["Filter by Date/Type"]
    FilterData --> ExportData["Export Report"]

    StartScan --> ScanProgress["View Scan Progress"]
    ScanProgress --> ScanComplete["Scan Complete"]
    ScanComplete --> Dashboard

    Dashboard --> SetAlerts["Configure Alerts"]
    SetAlerts --> AlertTriggered["Alert Triggered"]
    AlertTriggered --> ViewAlert["View Alert Details"]
    ViewAlert --> Dashboard

    Dashboard --> WorkStatus["Manage Work Status"]
    WorkStatus --> ImportCSV["Import CSV Data"]
    WorkStatus --> EditTask["Edit Task Progress"]
    WorkStatus --> ViewKanban["View Kanban Board"]
    EditTask --> UpdateProgress["Update Progress %"]
    UpdateProgress --> WorkStatus
```

---

## 13. 컴포넌트 구조

```mermaid
flowchart TB
    subgraph Components["React Component Structure"]
        App["App.tsx"]

        App --> Layout["Layout.tsx"]

        Layout --> Header["Header.tsx"]
        Layout --> Sidebar["Sidebar.tsx"]
        Layout --> Main["MainContent.tsx"]
        Layout --> Footer["Footer.tsx"]

        Main --> Dashboard["DashboardPage.tsx"]
        Main --> FolderView["FolderViewPage.tsx"]
        Main --> WorkStatus["WorkStatusPage.tsx"]
        Main --> History["HistoryPage.tsx"]
        Main --> Alerts["AlertsPage.tsx"]
        Main --> Settings["SettingsPage.tsx"]

        WorkStatus --> StatusTable["StatusTable.tsx"]
        WorkStatus --> KanbanBoard["KanbanBoard.tsx"]
        WorkStatus --> CSVImport["CSVImport.tsx"]

        Dashboard --> StatCards["StatCards.tsx"]
        Dashboard --> FolderTree["FolderTree.tsx"]
        Dashboard --> ChartPanel["ChartPanel.tsx"]

        ChartPanel --> PieChart["PieChart.tsx"]
        ChartPanel --> LineChart["LineChart.tsx"]
        ChartPanel --> BarChart["BarChart.tsx"]

        FolderTree --> TreeNode["TreeNode.tsx"]
        FolderTree --> TreeSearch["TreeSearch.tsx"]
    end
```

---

**이 문서는 Archive Statistics Dashboard의 UI/UX 설계를 Mermaid 다이어그램으로 시각화한 것입니다.**
