import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import { useAuth } from '../contexts/AuthContext';
import { portfoliosAPI, curationAPI } from '../services/api';

const DEFAULT_PORTFOLIO_SETTINGS = {
  showHeatmap: true,
  showSkills: true,
  showProjectDetails: true,
  showPortfolioItems: true,
  showProjects: true,
  showProfileSummary: true,
  skillsDisplayLimit: 10,
  projectDisplayMode: 'full', // 'full' or 'summary'
  heatmapTimeRange: 'auto', // 'auto', '1year', '2years', '3years'
  theme: 'default' // 'default', 'minimal', 'professional'
};

const formatTimestamp = (value) => {
  if (!value) return 'N/A';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

const UserProfileSummary = ({ 
  selectedPortfolioDetail, 
  orderedProjectList, 
  skillTags, 
  auth, 
  totalProjects,
  analysisType,
  isPrivateMode,
  updateSettings,
  portfolioSettings 
}) => {
  // Calculate overall role assessment
  const roleAssessment = useMemo(() => {
    const roles = orderedProjectList.map(p => p.curated_role || p.predicted_role).filter(Boolean);
    const roleFreq = roles.reduce((acc, role) => {
      acc[role] = (acc[role] || 0) + 1;
      return acc;
    }, {});
    
    if (Object.keys(roleFreq).length === 0) return null;
    
    const dominantRole = Object.entries(roleFreq)
      .sort(([,a], [,b]) => b - a)[0];
    
    const avgConfidence = orderedProjectList
      .filter(p => p.predicted_role_confidence)
      .reduce((sum, p) => sum + p.predicted_role_confidence, 0) / 
      orderedProjectList.filter(p => p.predicted_role_confidence).length;
    
    return {
      role: dominantRole[0],
      frequency: dominantRole[1],
      totalProjects: roles.length,
      confidence: avgConfidence || 0,
      diversity: Object.keys(roleFreq).length
    };
  }, [orderedProjectList]);

  // Top programming languages
  const topLanguages = useMemo(() => {
    const langFreq = orderedProjectList.reduce((acc, project) => {
      if (project.primary_language) {
        acc[project.primary_language] = (acc[project.primary_language] || 0) + 1;
      }
      return acc;
    }, {});
    
    return Object.entries(langFreq)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([lang, count]) => ({ language: lang, projects: count }));
  }, [orderedProjectList]);

  return (
    <section style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      borderRadius: '24px',
      padding: '40px',
      marginBottom: '32px',
      color: 'white',
      position: 'relative',
      overflow: 'hidden',
      border: isPrivateMode ? '3px dashed #8b5cf6' : 'none',
    }}>
      {/* Background Pattern */}
      <div style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: '100%',
        height: '100%',
        background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.05"%3E%3Ccircle cx="30" cy="30" r="4"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
        zIndex: 1
      }} />

      {/* Customization Controls */}
      {isPrivateMode && (
        <div style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          padding: '8px 12px',
          borderRadius: '8px',
          fontSize: '12px',
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
          zIndex: 10
        }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer', color: '#1f2937' }}>
            <input
              type="checkbox"
              checked={portfolioSettings.showProfileSummary !== false}
              onChange={(e) => updateSettings({ showProfileSummary: e.target.checked })}
            />
            Show Profile Summary
          </label>
        </div>
      )}

      {(portfolioSettings.showProfileSummary !== false) && (
        <div style={{ position: 'relative', zIndex: 2 }}>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
            <div>
              <div style={{
                fontSize: '14px',
                fontWeight: '600',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                opacity: 0.8,
                marginBottom: '8px'
              }}>
                Developer Profile
              </div>
              <h1 style={{
                margin: 0,
                fontSize: '42px',
                fontWeight: '800',
                background: 'linear-gradient(45deg, #ffffff, #f3f4f6)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                {auth.user?.email?.split('@')[0] ? `${auth.user.email.split('@')[0]}'s Portfolio` : 'Portfolio Owner'}
              </h1>
            </div>
            
            <div style={{
              padding: '16px 24px',
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              borderRadius: '16px',
              textAlign: 'center',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.2)'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', marginBottom: '4px' }}>
                {totalProjects}
              </div>
              <div style={{ fontSize: '12px', opacity: 0.8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Projects Analyzed
              </div>
            </div>
          </div>

          {/* Role & Skills Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '24px',
            marginBottom: '32px'
          }}>
            {/* Role Assessment Card */}
            {roleAssessment && (
              <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '16px',
                padding: '24px',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.2)'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '16px'
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '20px'
                  }}>
                    🎯
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
                      Primary Role
                    </h3>
                    <p style={{ margin: 0, fontSize: '13px', opacity: 0.7 }}>
                      Based on {roleAssessment.totalProjects} project{roleAssessment.totalProjects !== 1 ? 's' : ''} across all portfolios
                    </p>
                  </div>
                </div>
                
                <div style={{ marginBottom: '12px' }}>
                  <div style={{
                    fontSize: '20px',
                    fontWeight: '700',
                    marginBottom: '6px'
                  }}>
                    {roleAssessment.role}
                  </div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '13px',
                    opacity: 0.8
                  }}>
                    <div style={{
                      width: `${roleAssessment.confidence * 100}%`,
                      height: '4px',
                      backgroundColor: 'rgba(255, 255, 255, 0.6)',
                      borderRadius: '2px'
                    }} />
                    <span>{Math.round(roleAssessment.confidence * 100)}% confidence</span>
                  </div>
                </div>
                
                {roleAssessment.diversity > 1 && (
                  <div style={{
                    fontSize: '12px',
                    opacity: 0.7,
                    padding: '8px 12px',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px'
                  }}>
                    📊 {roleAssessment.diversity} role specializations detected
                  </div>
                )}
              </div>
            )}

            {/* Skills Highlight Card */}
            <div style={{
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '16px',
              padding: '24px',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.2)'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                marginBottom: '16px'
              }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '20px'
                }}>
                  ⚡
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
                    Core Skills
                  </h3>
                  <p style={{ margin: 0, fontSize: '13px', opacity: 0.7 }}>
                    Top {Math.min(skillTags.length, 8)} across all projects
                  </p>
                </div>
              </div>
              
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '8px'
              }}>
                {skillTags.slice(0, 8).map((skill, index) => (
                  <span
                    key={skill.skill || skill.name || index}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '20px',
                      backgroundColor: skill.curated ? 
                        'rgba(34, 197, 94, 0.2)' : 
                        'rgba(255, 255, 255, 0.2)',
                      fontSize: '12px',
                      fontWeight: '600',
                      border: skill.curated ? 
                        '1px solid rgba(34, 197, 94, 0.4)' : 
                        '1px solid rgba(255, 255, 255, 0.3)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    {skill.curated && '✨'}
                    {skill.skill || skill.name}
                  </span>
                ))}
              </div>
              
              {skillTags.length > 8 && (
                <p style={{ 
                  margin: '12px 0 0',
                  fontSize: '12px',
                  opacity: 0.7,
                  textAlign: 'center'
                }}>
                  +{skillTags.length - 8} more skills
                </p>
              )}
            </div>

            {/* Languages Card */}
            {topLanguages.length > 0 && (
              <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '16px',
                padding: '24px',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.2)'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '16px'
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '20px'
                  }}>
                    💻
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
                      Languages
                    </h3>
                    <p style={{ margin: 0, fontSize: '13px', opacity: 0.7 }}>
                      Primary technologies
                    </p>
                  </div>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {topLanguages.map((lang, index) => (
                    <div key={lang.language} style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '8px'
                    }}>
                      <span style={{ fontSize: '14px', fontWeight: '500' }}>
                        {lang.language}
                      </span>
                      <span style={{
                        fontSize: '12px',
                        opacity: 0.8,
                        padding: '2px 8px',
                        backgroundColor: 'rgba(255, 255, 255, 0.2)',
                        borderRadius: '12px'
                      }}>
                        {lang.projects} project{lang.projects !== 1 ? 's' : ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Call to Action */}
          <div style={{
            textAlign: 'center',
            padding: '20px',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '16px',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            <p style={{
              margin: '0 0 12px',
              fontSize: '16px',
              fontWeight: '500'
            }}>
              🚀 Explore detailed analysis of your projects below
            </p>
            <p style={{
              margin: 0,
              fontSize: '14px',
              opacity: 0.8
            }}>
              Dive into code quality metrics, project insights, and technical assessments
            </p>
          </div>
        </div>
      )}
    </section>
  );
};

const ActivityHeatmap = ({ portfolios, projectList }) => {
  const CELL = 13;
  const GAP  = 2;
  const [tooltip, setTooltip] = useState(null);   // { day, x, y }
  const [selectedYear, setSelectedYear] = useState(null);
  const scrollRef = useRef(null);

  const toLocalKey = (d) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

  const parseDate = (val) => {
    if (!val) return null;
    if (val instanceof Date) return Number.isNaN(val.getTime()) ? null : val;
    const s = String(val);
    const d = /^\d{4}-\d{2}-\d{2}/.test(s) ? new Date(`${s.slice(0, 10)}T00:00:00`) : new Date(s);
    return Number.isNaN(d.getTime()) ? null : d;
  };

  // Dynamic window: go back to the earliest project date, minimum 1 year, capped at 3 years
  const gridStart = useMemo(() => {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const maxBack  = new Date(today); maxBack.setFullYear(maxBack.getFullYear() - 3);
    const minBack  = new Date(today); minBack.setFullYear(minBack.getFullYear() - 1);
    let earliest = new Date(minBack); // always show at least 1 year
    for (const p of portfolios) {
      const d = parseDate(p.analysis_timestamp);
      if (d && d < earliest) earliest = new Date(d);
    }
    for (const proj of projectList) {
      for (const field of ['project_start_date', 'last_commit_date']) {
        const d = parseDate(proj[field]);
        if (d && d < earliest) earliest = new Date(d);
      }
    }
    if (earliest < maxBack) earliest = new Date(maxBack);
    earliest.setDate(earliest.getDate() - earliest.getDay());
    return earliest;
  }, [portfolios, projectList]);

  const WEEKS = useMemo(() => {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    return Math.min(156, Math.ceil((today - gridStart) / (7 * 86400000)) + 1);
  }, [gridStart]);

  // Build activity map + per-day project map from all temporal signals
  const { activityMap, dayProjectsMap } = useMemo(() => {
    const map     = new Map();
    const projMap = new Map(); // key -> Set<projectName>
    const today   = new Date(); today.setHours(0, 0, 0, 0);

    const addDay = (dateVal, weight, projName) => {
      const d = parseDate(dateVal);
      if (!d || d < gridStart || d > today) return;
      const key = toLocalKey(d);
      map.set(key, (map.get(key) ?? 0) + weight);
      if (projName) {
        if (!projMap.has(key)) projMap.set(key, new Set());
        projMap.get(key).add(projName);
      }
    };

    for (const proj of projectList) {
      const name        = proj.name || proj.repo_name || proj.repository || 'Project';
      const userCommits = Math.max(1,
        proj.target_user_stats?.commit_count ??
        proj.target_user_stats?.commits ??
        proj.total_commits ?? 1);

      addDay(proj.project_start_date,      7, name);
      addDay(proj.project_end_date,        7, name);
      addDay(proj.last_commit_date,        6, name);
      addDay(proj.target_user_last_commit, 6, name);

      for (const c of (Array.isArray(proj.contributors) ? proj.contributors : [])) {
        addDay(c.first_commit_date, 4, name);
        addDay(c.last_commit_date,  4, name);
      }

      const start = parseDate(proj.project_start_date);
      const end   = parseDate(proj.project_end_date ?? proj.last_commit_date);

      if (start && end && end >= start) {
        const spanDays       = Math.max(1, Math.round((end - start) / 86400000));
        const activeFrac     = Math.min(1, (proj.project_active_days ?? spanDays) / spanDays);
        const skipDays       = Math.max(1, Math.round(spanDays / Math.max(userCommits * activeFrac, 1)));
        const perDayWeight   = Math.max(2, userCommits / Math.max(spanDays / skipDays, 1));
        const effectiveStart = start < gridStart ? new Date(gridStart) : new Date(start);
        const dt = new Date(effectiveStart);
        let i = 0;
        while (dt <= end && dt <= today) {
          if (i % skipDays === 0) addDay(new Date(dt), perDayWeight, name);
          i++;
          dt.setDate(dt.getDate() + 1);
        }
      } else if (proj.last_commit_date) {
        addDay(proj.last_commit_date, Math.min(userCommits, 8), name);
      }
    }
    return { activityMap: map, dayProjectsMap: projMap };
  }, [portfolios, projectList, gridStart]);

  const { weeks, monthLabels, yearStarts } = useMemo(() => {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const weeksArr      = [];
    const months        = [];
    const yearStartsArr = [];
    const cur           = new Date(gridStart);
    let lastLabel = null, lastYear = -1, wi = 0;
    while (wi < WEEKS) {
      const week = [];
      for (let d = 0; d < 7; d++) {
        const key     = toLocalKey(cur);
        const inRange = cur >= gridStart && cur <= today;
        week.push({ date: new Date(cur), key, count: inRange ? (activityMap.get(key) ?? 0) : -1 });
        cur.setDate(cur.getDate() + 1);
      }
      const mon  = week[0].date.toLocaleString('en-US', { month: 'short' });
      const year = week[0].date.getFullYear();
      const lbl  = `${mon}-${year}`;
      if (lbl !== lastLabel && week[0].date <= today) {
        months.push({ weekIdx: wi, label: mon, year, showYear: mon === 'Jan' || wi === 0 });
        lastLabel = lbl;
      }
      if (year !== lastYear && week[0].date <= today) {
        yearStartsArr.push({ year, weekIdx: wi });
        lastYear = year;
      }
      weeksArr.push(week);
      wi++;
    }
    return { weeks: weeksArr, monthLabels: months, yearStarts: yearStartsArr };
  }, [activityMap, gridStart, WEEKS]);

  const maxCount = useMemo(
    () => activityMap.size === 0 ? 1 : Math.max(1, ...activityMap.values()),
    [activityMap]
  );

  const { longestStreak, currentStreak, totalCommits } = useMemo(() => {
    let best = 0, run = 0, cur2 = 0;
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const dt = new Date(gridStart);
    while (dt <= today) {
      const key = toLocalKey(dt);
      if (activityMap.has(key)) { run++; best = Math.max(best, run); } else { run = 0; }
      dt.setDate(dt.getDate() + 1);
    }
    const dt2 = new Date(today);
    while (activityMap.has(toLocalKey(dt2))) { cur2++; dt2.setDate(dt2.getDate() - 1); }
    const tc = projectList.reduce((s, p) => {
      // target_user_commits is computed in task_manager but NOT stored in raw_json;
      // try every known location in priority order
      const fromUserStats   = p.target_user_stats?.commit_count ?? p.target_user_stats?.commits ?? 0;
      const fromContribs    = Array.isArray(p.contributors)
        ? p.contributors.reduce((a, c) => a + (c.commit_count ?? c.commits ?? 0), 0)
        : 0;
      const fromTotal       = p.total_commits ?? 0;
      return s + Math.max(fromUserStats, fromContribs, fromTotal);
    }, 0);
    return { longestStreak: best, currentStreak: cur2, totalCommits: tc };
  }, [activityMap, gridStart, projectList]);

  const activeDays  = activityMap.size;
  const spanMonths  = Math.round((new Date() - gridStart) / (30 * 86400000));
  const spanLabel   = spanMonths >= 18 ? `${(spanMonths / 12).toFixed(1)} yrs` : `${spanMonths} months`;
  const renderCell = (day) => {
    if (day.count === -1) return <div key={day.key} style={{ width: CELL, height: CELL, flexShrink: 0 }} />;
    const { count, key, date } = day;
    const level   = count > 0 ? count / maxCount : 0;
    const dotSize = count === 0 ? 0 : Math.max(4, Math.round(level * (CELL - 3)));
    let dotColor = 'transparent', glow = 'none';
    if (level > 0) {
      if      (level < 0.25) dotColor = '#a5b4fc';
      else if (level < 0.5)  dotColor = '#818cf8';
      else if (level < 0.75) dotColor = '#6366f1';
      else                  { dotColor = '#4338ca'; glow = '0 0 6px 2px rgba(99,102,241,0.45)'; }
    }
    const label = count === 0
      ? date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      : `${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}: ${Math.round(count)} contributions`;
    return (
      <div
        key={key}
        title={label}
        style={{
          width: CELL, height: CELL, borderRadius: 3,
          backgroundColor: '#f1f5f9', flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: count > 0 ? 'crosshair' : 'default',
        }}
      >
        {dotSize > 0 && (
          <div style={{
            width: dotSize, height: dotSize, borderRadius: '50%',
            backgroundColor: dotColor, boxShadow: glow,
          }} />
        )}
      </div>
    );
  };

  if (portfolios.length === 0) {
    return (
      <div style={{ backgroundColor: 'white', padding: '32px', borderRadius: '20px',
        boxShadow: '0 20px 40px rgba(15,23,42,0.06)', marginBottom: '24px', textAlign: 'center' }}>
        <p style={{ color: '#9ca3af', fontSize: '14px', margin: 0 }}>
          No activity data yet. Upload and analyse projects to populate the heatmap.
        </p>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: 'white', padding: '32px', borderRadius: '20px',
      boxShadow: '0 20px 40px rgba(15, 23, 42, 0.06)', marginBottom: '24px' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
        marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ fontSize: '13px', fontWeight: '600', letterSpacing: '0.18em',
            textTransform: 'uppercase', color: '#6366f1', marginBottom: '6px' }}>Productivity</div>
          <h3 style={{ margin: '0 0 4px', fontSize: '20px', fontWeight: '700', color: '#0f172a' }}>
            Activity Heatmap
          </h3>
          <p style={{ margin: 0, fontSize: '13px', color: '#6b7280' }}>
            Full project activity history · {spanLabel}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          {[
            { value: activeDays,         label: 'Active Days'    },
            { value: currentStreak,      label: 'Current Streak' },
            { value: longestStreak,      label: 'Best Streak'    },
            { value: totalCommits,       label: 'Total Commits'  },
            { value: projectList.length, label: 'Projects'       },
          ].map(({ value, label }) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '22px', fontWeight: '700', color: '#4f46e5' }}>{value}</div>
              <div style={{ fontSize: '10px', color: '#9ca3af', textTransform: 'uppercase',
                letterSpacing: '0.1em', marginTop: '2px' }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div style={{ overflowX: 'auto' }}>
        <div style={{ display: 'inline-flex', minWidth: 'max-content' }}>
          {/* Day-of-week labels */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: GAP,
            paddingTop: 22, marginRight: 4, width: 26 }}>
            {['', 'Mon', '', 'Wed', '', 'Fri', ''].map((lbl, i) => (
              <div key={i} style={{ height: CELL, fontSize: 10, color: '#94a3b8',
                display: 'flex', alignItems: 'center', justifyContent: 'flex-end', paddingRight: 2 }}>
                {lbl}
              </div>
            ))}
          </div>

          <div>
            {/* Month labels */}
            <div style={{ display: 'flex', gap: GAP, height: 20, marginBottom: 2 }}>
              {weeks.map((_, wi) => {
                const ml = monthLabels.find((m) => m.weekIdx === wi);
                return (
                  <div key={wi} style={{ width: CELL, flexShrink: 0, fontSize: 10, overflow: 'visible',
                    whiteSpace: 'nowrap', color: ml?.showYear ? '#4f46e5' : '#64748b',
                    fontWeight: ml?.showYear ? '700' : 'normal' }}>
                    {ml ? (ml.showYear ? `${ml.label} ${ml.year}` : ml.label) : ''}
                  </div>
                );
              })}
            </div>
            {/* Cells */}
            <div style={{ display: 'flex', gap: GAP }}>
              {weeks.map((week, wi) => (
                <div key={wi} style={{ display: 'flex', flexDirection: 'column', gap: GAP }}>
                  {week.map((day) => renderCell(day))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '14px', justifyContent: 'flex-end' }}>
        <span style={{ fontSize: '11px', color: '#9ca3af' }}>Low</span>
        {[null, '#c7d2fe', '#a5b4fc', '#818cf8', '#6366f1', '#4338ca'].map((color, i) => (
          <div key={i} style={{ width: CELL, height: CELL, borderRadius: 3, backgroundColor: '#f1f5f9',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            {color && <div style={{ width: 2 + i * 2, height: 2 + i * 2, borderRadius: '50%',
              backgroundColor: color,
              boxShadow: i === 5 ? '0 0 6px 2px rgba(99,102,241,0.5)' : 'none' }} />}
          </div>
        ))}
        <span style={{ fontSize: '11px', color: '#9ca3af' }}>High</span>
      </div>
    </div>
  );
};

const Portfolio = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();

  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(null);
  const [selectedPortfolioDetail, setSelectedPortfolioDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState('');
  const [detailError, setDetailError] = useState('');
  // Cache of all fetched portfolio details (uuid → detail) for the heatmap
  const [allDetails, setAllDetails] = useState(new Map());
  const [deletingIds, setDeletingIds] = useState({});
  const [notification, setNotification] = useState(null);

  // Curation settings
  const [curationSettings, setCurationSettings] = useState(null);

  // Private Mode State for Portfolio Customization
  const [isPrivateMode, setIsPrivateMode] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [portfolioSettings, setPortfolioSettings] = useState({ ...DEFAULT_PORTFOLIO_SETTINGS });
  const [livePortfolioSettings, setLivePortfolioSettings] = useState({ ...DEFAULT_PORTFOLIO_SETTINGS });

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const loadPortfolios = useCallback(async () => {
    setError('');
    setLoading(true);
    setSelectedPortfolioDetail(null);
    setDetailError('');
    setAllDetails(new Map());
    try {
      const data = await portfoliosAPI.listPortfolios();
      setPortfolios(data ?? []);
      setSelectedPortfolioId(data?.[0]?.analysis_uuid ?? null);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load portfolios');
      setPortfolios([]);
      setSelectedPortfolioId(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    loadPortfolios();

    // Load curation settings
    curationAPI.getSettings()
      .then((settings) => setCurationSettings(settings))
      .catch(() => setCurationSettings(null));

    // Load portfolio settings
    loadPortfolioSettings();
  }, [isAuthenticated, navigate, loadPortfolios]);

  // Portfolio Settings Management
  const loadPortfolioSettings = async () => {
    try {
      const response = await portfoliosAPI.getPortfolioSettings?.() || {};
      const settings = response.data || response;
      const mergedSettings = { ...DEFAULT_PORTFOLIO_SETTINGS, ...settings };
      setPortfolioSettings(mergedSettings);
      setLivePortfolioSettings(mergedSettings);
    } catch (error) {
      // Use defaults if no settings found
      console.log('Using default portfolio settings');
      setLivePortfolioSettings({ ...DEFAULT_PORTFOLIO_SETTINGS });
    }
  };

  const savePortfolioSettings = async () => {
    try {
      await portfoliosAPI.savePortfolioSettings?.(portfolioSettings);
      setLivePortfolioSettings({ ...portfolioSettings });
      setHasUnsavedChanges(false);
      showNotification('Portfolio settings saved successfully!', 'success');
      setIsPrivateMode(false);
    } catch (error) {
      console.error('Error saving portfolio settings:', error);
      showNotification('Error saving portfolio settings. Please try again.', 'error');
    }
  };

  const refreshPortfolios = async () => {
    try {
      await loadPortfolios();
      showNotification('Portfolio data refreshed successfully!', 'success');
    } catch (error) {
      showNotification('Failed to refresh portfolio data', 'error');
    }
  };

  const togglePrivateMode = () => {
    // If exiting preview mode and there are unsaved changes, ask for confirmation
    if (isPrivateMode && hasUnsavedChanges) {
      const confirm = window.confirm('You have unsaved changes. Do you want to discard them and exit preview mode?');
      if (!confirm) return;
      // Revert to live settings
      if (livePortfolioSettings) {
        setPortfolioSettings({ ...livePortfolioSettings });
      }
      setHasUnsavedChanges(false);
    }
    setIsPrivateMode(!isPrivateMode);
  };

  const exitPreviewMode = () => {
    if (hasUnsavedChanges) {
      const confirm = window.confirm('You have unsaved changes. Do you want to discard them and exit preview mode?');
      if (!confirm) return;
      if (livePortfolioSettings) {
        setPortfolioSettings({ ...livePortfolioSettings });
      }
      setHasUnsavedChanges(false);
    }
    setIsPrivateMode(false);
  };

  const updateSettings = (newSettings) => {
    setPortfolioSettings(prev => ({ ...prev, ...newSettings }));
    setHasUnsavedChanges(true);
  };

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && isAuthenticated) {
        loadPortfolios();
      }
    };

    const handleFocus = () => {
      if (isAuthenticated) {
        loadPortfolios();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [isAuthenticated, loadPortfolios]);

  useEffect(() => {
    if (!selectedPortfolioId) {
      setSelectedPortfolioDetail(null);
      setDetailError('');
      return;
    }

    let cancelled = false;
    setDetailLoading(true);
    setDetailError('');
    setSelectedPortfolioDetail(null);

    portfoliosAPI
      .getPortfolioDetail(selectedPortfolioId)
      .then((detail) => {
        if (!cancelled) {
          setSelectedPortfolioDetail(detail);
          // Cache this detail for the heatmap
          setAllDetails((prev) => new Map(prev).set(selectedPortfolioId, detail));
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setDetailError(
            err?.response?.data?.detail || err?.message || 'Unable to load portfolio details'
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setDetailLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedPortfolioId]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && isAuthenticated) {
        loadPortfolios();
      }
    };

    const handleWindowFocus = () => {
      if (isAuthenticated) {
        loadPortfolios();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleWindowFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleWindowFocus);
    };
  }, [isAuthenticated, loadPortfolios]);

  useEffect(() => {
    if (portfolios.length === 0) {
      setAllDetails(new Map());
      return;
    }
    
    let cancelled = false;
    const currentUuids = new Set(portfolios.map((p) => p.analysis_uuid).filter(Boolean));
    
    setAllDetails((prev) => {
      const cleaned = new Map();
      for (const [uuid, detail] of prev.entries()) {
        if (currentUuids.has(uuid)) {
          cleaned.set(uuid, detail);
        }
      }
      return cleaned;
    });
    
    const uuidsArray = Array.from(currentUuids);
    uuidsArray.forEach((uuid) => {
      setAllDetails((prev) => {
        if (prev.has(uuid)) return prev; // already cached
        portfoliosAPI.getPortfolioDetail(uuid).then((detail) => {
          if (!cancelled) {
            setAllDetails((current) => new Map(current).set(uuid, detail));
          }
        }).catch(() => {}); 
        return prev;
      });
    });
    
    return () => { cancelled = true; };
  }, [portfolios]);

  const selectedSummaryEntry = useMemo(
    () => portfolios.find((portfolio) => portfolio.analysis_uuid === selectedPortfolioId) ?? null,
    [portfolios, selectedPortfolioId]
  );

  const totalProjects =
    selectedPortfolioDetail?.total_projects ?? selectedSummaryEntry?.total_projects ?? 0;
  const analysisType =
    selectedPortfolioDetail?.analysis_type ?? selectedSummaryEntry?.analysis_type ?? 'N/A';
  const heroTimestamp =
    selectedPortfolioDetail?.analysis_timestamp ?? selectedSummaryEntry?.analysis_timestamp ?? null;

  const projectList = selectedPortfolioDetail?.projects ?? [];
  const portfolioItems =
    selectedPortfolioDetail?.portfolio_items ||
    selectedPortfolioDetail?.items ||
    selectedPortfolioDetail?.portfolio ||
    [];
  // Use curated highlighted skills if available, otherwise auto-derive
  const skillTags = useMemo(() => {
    const curatedSkills = curationSettings?.highlighted_skills;
    if (Array.isArray(curatedSkills) && curatedSkills.length > 0) {
      return curatedSkills.map((skill) => ({ skill, count: null, curated: true }));
    }

    const rawSkills = selectedPortfolioDetail?.skills;
    if (Array.isArray(rawSkills) && rawSkills.length > 0) {
      return rawSkills;
    }

    const skillCounts = new Map();
    for (const item of portfolioItems) {
      const skills = item?.skills_exercised;
      const normalizedSkills = Array.isArray(skills)
        ? skills
        : typeof skills === 'string'
          ? skills.split(',').map((skill) => skill.trim())
          : [];
      for (const skill of normalizedSkills) {
        if (!skill) continue;
        skillCounts.set(skill, (skillCounts.get(skill) ?? 0) + 1);
      }
    }

    return [...skillCounts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 10)
      .map(([skill, count]) => ({ skill, count }));
  }, [selectedPortfolioDetail, portfolioItems, curationSettings]);

  // Apply custom project order from curation settings
  const orderedPortfolioItems = useMemo(() => {
    if (!Array.isArray(portfolioItems) || portfolioItems.length === 0) return portfolioItems;
    const orderIds = curationSettings?.custom_project_order;
    if (!Array.isArray(orderIds) || orderIds.length === 0) return portfolioItems;

    const itemsCopy = [...portfolioItems];
    itemsCopy.sort((a, b) => {
      const aId = a.project_id ?? a.id;
      const bId = b.project_id ?? b.id;
      const aIdx = orderIds.indexOf(aId);
      const bIdx = orderIds.indexOf(bId);
      if (aIdx === -1 && bIdx === -1) return 0;
      if (aIdx === -1) return 1;
      if (bIdx === -1) return -1;
      return aIdx - bIdx;
    });
    return itemsCopy;
  }, [portfolioItems, curationSettings]);

  const orderedProjectList = useMemo(() => {
    if (!Array.isArray(projectList) || projectList.length === 0) return projectList;
    const orderIds = curationSettings?.custom_project_order;
    if (!Array.isArray(orderIds) || orderIds.length === 0) return projectList;

    const listCopy = [...projectList];
    listCopy.sort((a, b) => {
      const aId = a.id;
      const bId = b.id;
      const aIdx = orderIds.indexOf(aId);
      const bIdx = orderIds.indexOf(bId);
      if (aIdx === -1 && bIdx === -1) return 0;
      if (aIdx === -1) return 1;
      if (bIdx === -1) return -1;
      return aIdx - bIdx;
    });
    return listCopy;
  }, [projectList, curationSettings]);

  const allProjectsForHeatmap = useMemo(() => {
    const seen = new Set();
    const result = [];
    for (const detail of allDetails.values()) {
      for (const proj of (detail?.projects ?? [])) {
        const uid = proj.id ?? proj.name ?? JSON.stringify(proj);
        if (!seen.has(uid)) { seen.add(uid); result.push(proj); }
      }
    }
    return result;
  }, [allDetails]);

  // Aggregate all portfolio items from all portfolios for comprehensive skill analysis
  const allPortfolioItems = useMemo(() => {
    const result = [];
    for (const detail of allDetails.values()) {
      const items = detail?.portfolio_items || detail?.items || detail?.portfolio || [];
      result.push(...items);
    }
    return result;
  }, [allDetails]);

  // Aggregate skills from ALL portfolios
  const aggregatedSkillTags = useMemo(() => {
    const skillCounts = new Map();
    
    // First check for any curated skills from curation settings
    const curatedSkills = curationSettings?.highlighted_skills;
    if (Array.isArray(curatedSkills) && curatedSkills.length > 0) {
      return curatedSkills.map((skill) => ({ skill, count: null, curated: true }));
    }

    // Aggregate skills from all portfolio details
    for (const detail of allDetails.values()) {
      const rawSkills = detail?.skills;
      if (Array.isArray(rawSkills)) {
        for (const skillObj of rawSkills) {
          const skillName = skillObj.skill || skillObj.name;
          if (skillName) {
            const currentCount = skillCounts.get(skillName) || 0;
            const skillCount = skillObj.count || 1;
            skillCounts.set(skillName, currentCount + skillCount);
          }
        }
      }

      // Also get skills from portfolio items  
      const items = detail?.portfolio_items || detail?.items || detail?.portfolio || [];
      for (const item of items) {
        const skills = item?.skills_exercised;
        const normalizedSkills = Array.isArray(skills)
          ? skills
          : typeof skills === 'string'
            ? skills.split(',').map((skill) => skill.trim())
            : [];
        for (const skill of normalizedSkills) {
          if (!skill) continue;
          skillCounts.set(skill, (skillCounts.get(skill) ?? 0) + 1);
        }
      }
    }

    return [...skillCounts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 15)  // Show more skills since we're aggregating
      .map(([skill, count]) => ({ skill, count }));
  }, [allDetails, curationSettings]);

  // Calculate total projects from all portfolios
  const totalAggregatedProjects = useMemo(() => {
    return allProjectsForHeatmap.length;
  }, [allProjectsForHeatmap]);

  // Showcase project IDs → rank (1, 2, 3)
  const showcaseRanks = useMemo(() => {
    const ids = curationSettings?.showcase_project_ids ?? [];
    const map = new Map();
    ids.forEach((id, i) => map.set(id, i + 1));
    return map;
  }, [curationSettings]);

  // Selected comparison attributes
  const selectedAttributes = useMemo(() => {
    return new Set(curationSettings?.comparison_attributes ?? []);
  }, [curationSettings]);

  const handleSelectPortfolio = (portfolioId) => {
    if (portfolioId === selectedPortfolioId) return;
    setSelectedPortfolioId(portfolioId);
  };

  const handleDeletePortfolio = async (portfolioId, portfolioName) => {
    const name = portfolioName || 'this portfolio analysis';
    const ok = window.confirm(
      `Delete ${name}?\n\nThis will remove the analysis but keep your original projects.`
    );
    if (!ok) return;

    setDeletingIds(prev => ({ ...prev, [portfolioId]: true }));
    
    try {
      await portfoliosAPI.deletePortfolio(portfolioId);
      
      // Remove from portfolios list
      setPortfolios(prev => prev.filter(p => p.analysis_uuid !== portfolioId));
      
      // Clear related details
      setAllDetails(prev => {
        const updated = new Map(prev);
        updated.delete(portfolioId);
        return updated;
      });
      
      // Select another portfolio if we deleted the current one
      if (selectedPortfolioId === portfolioId) {
        const remaining = portfolios.filter(p => p.analysis_uuid !== portfolioId);
        setSelectedPortfolioId(remaining[0]?.analysis_uuid || null);
        setSelectedPortfolioDetail(null);
      }
      
      setNotification({
        type: 'success',
        message: 'Portfolio analysis deleted successfully'
      });
      
    } catch (error) {
      console.error('Failed to delete portfolio:', error);
      const message = error?.response?.data?.detail || error?.message || 'Failed to delete portfolio analysis';
      setNotification({
        type: 'error', 
        message
      });
    } finally {
      setDeletingIds(prev => {
        const copy = { ...prev };
        delete copy[portfolioId];
        return copy;
      });
    }
  };

  // Auto-hide notifications
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const renderJsonBlock = (data) => (
    <pre
      style={{
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        fontSize: '12px',
        color: '#111827',
        backgroundColor: '#f9fafb',
        padding: '12px',
        borderRadius: '10px',
        border: '1px solid #e5e7eb',
        maxHeight: '400px',
        overflow: 'auto',
      }}
    >
      {JSON.stringify(data, null, 2)}
    </pre>
  );

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#fafafa',
      position: 'relative'
    }}>
      {/* CSS Animation Styles */}
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
      
      <Navigation />
      
      {/* Notification Toast */}
      {notification && (
        <div style={{
          position: 'fixed',
          top: '24px',
          right: '24px',
          zIndex: 1000,
          padding: '12px 16px',
          borderRadius: '8px',
          backgroundColor: notification.type === 'success' ? '#f0fdf4' : '#fef2f2',
          border: `1px solid ${notification.type === 'success' ? '#bbf7d0' : '#fecaca'}`,
          color: notification.type === 'success' ? '#166534' : '#dc2626',
          fontSize: '14px',
          fontWeight: '500',
          boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          {notification.type === 'success' ? '✓' : '⚠️'} {notification.message}
          <button
            onClick={() => setNotification(null)}
            style={{
              background: 'none',
              border: 'none',
              color: 'inherit',
              fontSize: '16px',
              cursor: 'pointer',
              marginLeft: '8px',
              padding: '0 4px'
            }}
          >
            ×
          </button>
        </div>
      )}
      
      {/* Private Mode Banner */}
      {isPrivateMode && (
        <div style={{
          position: 'fixed',
          top: '80px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: '#8b5cf6',
          color: 'white',
          padding: '8px 16px',
          borderRadius: '20px',
          fontSize: '14px',
          fontWeight: '600',
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          🎨 Portfolio Preview Mode
          {hasUnsavedChanges && (
            <span style={{
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              padding: '2px 8px',
              borderRadius: '10px',
              fontSize: '12px'
            }}>
              Unsaved
            </span>
          )}
        </div>
      )}
      
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px 24px 48px' }}>
        {/* Portfolio Header with Private Mode Controls */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '32px',
          backgroundColor: 'white',
          padding: '20px 24px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <div>
            <h1 style={{
              margin: '0 0 4px 0',
              fontSize: '28px',
              fontWeight: '700',
              color: '#1a1a1a'
            }}>
              Portfolio Showcase
            </h1>
            <p style={{
              margin: 0,
              color: '#6b7280',
              fontSize: '14px'
            }}>
              {isPrivateMode ? 'Preview your changes - make edits and see how they look before publishing' : 'Your professional project showcase'}
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            {isPrivateMode && (
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={exitPreviewMode}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '8px',
                    border: '1px solid #e5e5e5',
                    backgroundColor: 'white',
                    color: '#737373',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  Discard Changes
                </button>
                <button
                  onClick={savePortfolioSettings}
                  disabled={!hasUnsavedChanges}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '8px',
                    border: '1px solid #8b5cf6',
                    backgroundColor: hasUnsavedChanges ? '#8b5cf6' : '#e5e5e5',
                    color: hasUnsavedChanges ? 'white' : '#737373',
                    cursor: hasUnsavedChanges ? 'pointer' : 'not-allowed',
                    fontSize: '14px',
                    fontWeight: '600'
                  }}
                >
                  Publish Changes
                </button>
              </div>
            )}
            
            <button
              onClick={refreshPortfolios}
              style={{
                padding: '10px 16px',
                borderRadius: '8px',
                border: '1px solid #e5e5e5',
                backgroundColor: 'white',
                color: '#737373',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
              title="Refresh portfolio data"
            >
              🔄 Refresh
            </button>
            
            <button
              onClick={togglePrivateMode}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                border: isPrivateMode ? '2px solid #8b5cf6' : '1px solid #e5e5e5',
                backgroundColor: isPrivateMode ? '#f3f4f6' : 'white',
                color: isPrivateMode ? '#8b5cf6' : '#1a1a1a',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {isPrivateMode ? 'Exit Preview' : '🎨 Preview Changes'}
            </button>
          </div>
        </div>
        {loading ? (
          <div
            style={{
              backgroundColor: 'white',
              padding: '40px',
              borderRadius: '16px',
              boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)',
              textAlign: 'center',
            }}
          >
            <p style={{ margin: 0, fontSize: '18px', color: '#4b5563' }}>Loading portfolios...</p>
          </div>
        ) : error ? (
          <div
            style={{
              backgroundColor: '#fee2e2',
              color: '#991b1b',
              padding: '24px',
              borderRadius: '16px',
              boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)',
            }}
          >
            <p style={{ margin: 0, fontWeight: '600' }}>Error loading portfolios</p>
            <p style={{ margin: '8px 0 0' }}>{error}</p>
            <button
              type="button"
              onClick={refreshPortfolios}
              style={{
                marginTop: '12px',
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: '#1d4ed8',
                color: 'white',
                cursor: 'pointer',
              }}
            >
              Retry
            </button>
          </div>
        ) : portfolios.length === 0 ? (
          <div
            style={{
              backgroundColor: 'white',
              padding: '40px',
              borderRadius: '16px',
              textAlign: 'center',
              boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)',
            }}
          >
            <h2 style={{ margin: '0 0 12px', fontSize: '28px', color: '#111827' }}>
              No portfolio analyses available
            </h2>
            <p style={{ margin: 0, color: '#4b5563' }}>
              Upload your project ZIP on the dashboard to start analyzing your work.
            </p>
          </div>
        ) : (
          <>
            {/* Interactive User Profile Summary */}
            <UserProfileSummary 
              selectedPortfolioDetail={selectedPortfolioDetail}
              orderedProjectList={allProjectsForHeatmap}  // Use ALL projects
              skillTags={aggregatedSkillTags}  // Use aggregated skills
              auth={{ user }}
              totalProjects={totalAggregatedProjects}  // Use total from all portfolios
              analysisType={analysisType}
              isPrivateMode={isPrivateMode}
              updateSettings={updateSettings}
              portfolioSettings={portfolioSettings}
            />
            
            {/* Activity Heatmap - Customizable */}
            {(portfolioSettings.showHeatmap || isPrivateMode) && (
              <div style={{ 
                position: 'relative',
                border: isPrivateMode ? '2px dashed #8b5cf6' : 'none',
                borderRadius: isPrivateMode ? '12px' : '0',
                padding: isPrivateMode ? '12px' : '0',
                backgroundColor: isPrivateMode ? 'rgba(139, 92, 246, 0.02)' : 'transparent'
              }}>
                {isPrivateMode && (
                  <div style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    backgroundColor: 'white',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    border: '1px solid #e5e5e5',
                    fontSize: '12px',
                    display: 'flex',
                    gap: '8px',
                    alignItems: 'center',
                    zIndex: 10
                  }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={portfolioSettings.showHeatmap}
                        onChange={(e) => updateSettings({ showHeatmap: e.target.checked })}
                      />
                      Show Heatmap
                    </label>
                  </div>
                )}
                {portfolioSettings.showHeatmap ? (
                  <ActivityHeatmap portfolios={portfolios} projectList={allProjectsForHeatmap} />
                ) : (
                  isPrivateMode && (
                    <div style={{
                      backgroundColor: 'white',
                      borderRadius: '12px',
                      border: '1px solid #e5e7eb',
                      padding: '20px',
                      color: '#6b7280',
                      marginTop: '8px'
                    }}>
                      Heatmap section is hidden
                    </div>
                  )
                )}
              </div>
            )}
            
            <div
              style={{
                display: 'grid',
                gap: '24px',
                gridTemplateColumns: '2fr 1fr',
                alignItems: 'stretch',
              }}
            >
            <section
              style={{
                backgroundColor: 'white',
                padding: '32px',
                borderRadius: '20px',
                boxShadow: '0 20px 40px rgba(15, 23, 42, 0.06)',
                border: isPrivateMode ? '2px dashed #8b5cf6' : 'none',
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    letterSpacing: '0.2em',
                    textTransform: 'uppercase',
                    color: '#6366f1',
                    marginBottom: '12px',
                  }}
                >
                  Portfolio
                </div>
                <h1
                  style={{
                    margin: '0 0 8px',
                    fontSize: '36px',
                    color: '#0f172a',
                    fontWeight: '700',
                  }}
                >
                  Portfolio Snapshot
                </h1>
                <p style={{ margin: 0, color: '#4b5563' }}>
                  Latest analysis run: {formatTimestamp(heroTimestamp)}
                </p>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                  gap: '16px',
                  marginTop: '24px',
                }}
              >
                <div
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: '1px solid #e5e7eb',
                    backgroundColor: '#f9fafb',
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: '12px',
                      letterSpacing: '0.2em',
                      textTransform: 'uppercase',
                      color: '#6b7280',
                    }}
                  >
                    Projects
                  </p>
                  <p style={{ margin: '8px 0 0', fontSize: '28px', fontWeight: '700', color: '#111827' }}>
                    {totalProjects}
                  </p>
                </div>
                <div
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: '1px solid #e5e7eb',
                    backgroundColor: '#fdf2f8',
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: '12px',
                      letterSpacing: '0.2em',
                      textTransform: 'uppercase',
                      color: '#be185d',
                    }}
                  >
                    Analysis Type
                  </p>
                  <p style={{ margin: '8px 0 0', fontSize: '20px', fontWeight: '600', color: '#111827' }}>
                    {analysisType.toUpperCase()}
                  </p>
                </div>
              </div>

              <div style={{ 
                marginTop: '32px',
                position: 'relative',
                border: isPrivateMode ? '2px dashed #8b5cf6' : 'none',
                borderRadius: isPrivateMode ? '12px' : '0',
                padding: isPrivateMode ? '12px' : '0',
                backgroundColor: isPrivateMode ? 'rgba(139, 92, 246, 0.02)' : 'transparent'
              }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  marginBottom: '8px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 style={{ margin: 0, fontSize: '18px', color: '#0f172a' }}>Highlighted Skills</h3>
                    {skillTags.length > 0 && skillTags[0]?.curated && (
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '999px',
                        backgroundColor: '#f0fdf4',
                        color: '#166534',
                        fontSize: '11px',
                        fontWeight: '600',
                        border: '1px solid #bbf7d0',
                      }}>Curated</span>
                    )}
                  </div>
                  
                  {isPrivateMode && (
                    <div style={{
                      display: 'flex',
                      gap: '8px',
                      alignItems: 'center',
                      fontSize: '12px',
                      backgroundColor: 'white',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      border: '1px solid #e5e5e5'
                    }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={portfolioSettings.showSkills}
                          onChange={(e) => updateSettings({ showSkills: e.target.checked })}
                        />
                        Show Skills
                      </label>
                    </div>
                  )}
                </div>
                
                {portfolioSettings.showSkills && skillTags.length > 0 ? (
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '10px',
                      marginTop: '12px',
                    }}
                  >
                    {skillTags.map((skill) => (
                      <span
                        key={skill.skill || skill.name}
                        style={{
                          padding: '6px 12px',
                          borderRadius: '999px',
                          backgroundColor: skill.curated ? '#f0fdf4' : '#eef2ff',
                          color: skill.curated ? '#166534' : '#4338ca',
                          fontSize: '13px',
                          fontWeight: '600',
                          border: skill.curated ? '1px solid #bbf7d0' : 'none',
                        }}
                      >
                        {skill.skill || skill.name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p style={{ margin: '8px 0 0', color: '#6b7280' }}>
                    {!portfolioSettings.showSkills && isPrivateMode 
                      ? 'Skills section is hidden' 
                      : 'No skill highlights were captured for this run yet.'}
                  </p>
                )}
              </div>

              <div style={{ 
                marginTop: '32px',
                position: 'relative',
                border: isPrivateMode ? '2px dashed #8b5cf6' : 'none',
                borderRadius: isPrivateMode ? '12px' : '0',
                padding: isPrivateMode ? '12px' : '0',
                backgroundColor: isPrivateMode ? 'rgba(139, 92, 246, 0.02)' : 'transparent'
              }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  marginBottom: '8px'
                }}>
                  <h3 style={{ margin: 0, fontSize: '18px', color: '#0f172a' }}>Portfolio Items</h3>
                  
                  {isPrivateMode && (
                    <div style={{
                      display: 'flex',
                      gap: '8px',
                      alignItems: 'center',
                      fontSize: '12px',
                      backgroundColor: 'white',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      border: '1px solid #e5e5e5'
                    }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={portfolioSettings.showPortfolioItems}
                          onChange={(e) => updateSettings({ showPortfolioItems: e.target.checked })}
                        />
                        Show Portfolio Items
                      </label>
                    </div>
                  )}
                </div>
                
                {portfolioSettings.showPortfolioItems && Array.isArray(orderedPortfolioItems) && orderedPortfolioItems.length > 0 ? (
                  <div
                    style={{
                      marginTop: '16px',
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                      gap: '16px',
                    }}
                  >
                    {orderedPortfolioItems.map((item, idx) => (
                      (() => {
                        const itemId = item.project_id ?? item.id;
                        const showcaseRank = showcaseRanks.get(itemId);
                        const isShowcase = !!showcaseRank;
                        const qualityScore =
                          item.quality_score ?? item.project_statistics?.quality_score;
                        const sophisticationLevel =
                          item.sophistication_level ?? item.project_statistics?.sophistication_level;
                        const techStack = Array.isArray(item.tech_stack)
                          ? item.tech_stack.join(', ')
                          : item.tech_stack;
                        const skillsExercised = Array.isArray(item.skills_exercised)
                          ? item.skills_exercised.join(', ')
                          : item.skills_exercised;

                        // Attribute visibility based on curation
                        const showAttr = (key) => selectedAttributes.size === 0 || selectedAttributes.has(key);

                        return (
                          <div
                            key={`portfolio-item-${idx}`}
                            style={{
                              borderRadius: '14px',
                              border: isShowcase ? '2px solid #f59e0b' : '1px solid #e5e7eb',
                              padding: '16px',
                              backgroundColor: isShowcase ? '#fffbeb' : 'white',
                              position: 'relative',
                            }}
                          >
                            {isShowcase && (
                              <span style={{
                                position: 'absolute',
                                top: '-10px',
                                right: '12px',
                                padding: '2px 8px',
                                borderRadius: '999px',
                                backgroundColor: '#f59e0b',
                                color: 'white',
                                fontSize: '11px',
                                fontWeight: '700',
                              }}>⭐ Top {showcaseRank}</span>
                            )}
                            <strong style={{ display: 'block', marginBottom: '6px', color: '#0f172a' }}>
                              {item.title || item.project_name || `Item ${idx + 1}`}
                            </strong>
                            {item.text_summary && (
                              <p style={{ margin: 0, color: '#374151', fontSize: '14px', lineHeight: 1.5 }}>
                                {item.text_summary}
                              </p>
                            )}
                            {techStack && showAttr('primary_language') && (
                              <p style={{ margin: '8px 0 0', color: '#6b7280', fontSize: '13px' }}>
                                Tech stack: {techStack}
                              </p>
                            )}
                            {skillsExercised && (
                              <p style={{ margin: '6px 0 0', color: '#6b7280', fontSize: '13px' }}>
                                Skills: {skillsExercised}
                              </p>
                            )}
                            {qualityScore !== undefined && showAttr('test_coverage_estimate') && (
                              <p style={{ margin: '6px 0 0', color: '#6b7280', fontSize: '13px' }}>
                                Quality score: {qualityScore}
                              </p>
                            )}
                            {sophisticationLevel && (
                              <p style={{ margin: '6px 0 0', color: '#6b7280', fontSize: '13px' }}>
                                Sophistication: {sophisticationLevel}
                              </p>
                            )}
                            {(item.curated_role || item.predicted_role) && (
                              <p style={{
                                margin: '8px 0 0',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '6px',
                                padding: '3px 10px',
                                borderRadius: '999px',
                                backgroundColor: item.curated_role ? '#f0fdf4' : '#eef2ff',
                                border: `1px solid ${item.curated_role ? '#bbf7d0' : '#c7d2fe'}`,
                                fontSize: '13px',
                                fontWeight: '600',
                                color: item.curated_role ? '#166534' : '#3730a3',
                              }}>
                                {item.curated_role || item.predicted_role}
                                {!item.curated_role && item.predicted_role_confidence != null && (
                                  <span style={{ fontSize: '11px', opacity: 0.8 }}>
                                    {Math.round(item.predicted_role_confidence * 100)}%
                                  </span>
                                )}
                              </p>
                            )}
                          </div>
                        );
                      })()
                    ))}
                  </div>
                ) : (
                  <p style={{ marginTop: '12px', color: '#6b7280' }}>
                    {!portfolioSettings.showPortfolioItems && isPrivateMode 
                      ? 'Portfolio items section is hidden' 
                      : 'No portfolio items were returned by the backend yet.'}
                  </p>
                )}
              </div>

              <div style={{ 
                marginTop: '32px',
                position: 'relative',
                border: isPrivateMode ? '2px dashed #8b5cf6' : 'none',
                borderRadius: isPrivateMode ? '12px' : '0',
                padding: isPrivateMode ? '12px' : '0',
                backgroundColor: isPrivateMode ? 'rgba(139, 92, 246, 0.02)' : 'transparent'
              }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  marginBottom: '8px'
                }}>
                  <h3 style={{ margin: 0, fontSize: '18px', color: '#0f172a' }}>Projects</h3>
                  
                  {isPrivateMode && (
                    <div style={{
                      display: 'flex',
                      gap: '8px',
                      alignItems: 'center',
                      fontSize: '12px',
                      backgroundColor: 'white',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      border: '1px solid #e5e5e5'
                    }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={portfolioSettings.showProjects}
                          onChange={(e) => updateSettings({ showProjects: e.target.checked })}
                        />
                        Show Projects
                      </label>
                    </div>
                  )}
                </div>
                
                {portfolioSettings.showProjects && orderedProjectList.length > 0 ? (
                  <ul
                    style={{
                      margin: '16px 0 0',
                      paddingLeft: '18px',
                      color: '#1f2937',
                      lineHeight: 1.6,
                    }}
                  >
                    {orderedProjectList.map((project, index) => {
                      const showcaseRank = showcaseRanks.get(project.id);
                      const isShowcase = !!showcaseRank;
                      return (
                        <li key={`${project.project_name}-${index}`} style={{ marginBottom: '12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <strong style={{ fontSize: '16px', color: '#0f172a' }}>
                              {project.project_name || project.name || 'Unnamed project'}
                            </strong>
                            {isShowcase && (
                              <span style={{
                                padding: '1px 6px',
                                borderRadius: '999px',
                                backgroundColor: '#fef3c7',
                                color: '#b45309',
                                fontSize: '11px',
                                fontWeight: '600',
                              }}>⭐ Top {showcaseRank}</span>
                            )}
                          </div>
                          <span style={{ fontSize: '13px', color: '#6b7280' }}>
                            {project.primary_language || 'Language unknown'} •{' '}
                            {project.total_files ?? '0'} files
                            {(project.curated_role || project.predicted_role) && (
                              <span style={{
                                marginLeft: '8px',
                                padding: '1px 8px',
                                borderRadius: '999px',
                                backgroundColor: project.curated_role ? '#f0fdf4' : '#eef2ff',
                                color: project.curated_role ? '#166534' : '#3730a3',
                                fontSize: '11px',
                                fontWeight: '600',
                                border: `1px solid ${project.curated_role ? '#bbf7d0' : '#c7d2fe'}`,
                              }}>
                                {project.curated_role || project.predicted_role}
                                {!project.curated_role && project.predicted_role_confidence != null
                                  ? ` (${Math.round(project.predicted_role_confidence * 100)}%)`
                                  : ''}
                              </span>
                            )}
                          </span>
                          {project.summary && (
                            <p style={{ margin: '6px 0 0', fontSize: '13px', color: '#374151' }}>
                              {project.summary}
                            </p>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p style={{ marginTop: '12px', color: '#6b7280' }}>
                    {!portfolioSettings.showProjects && isPrivateMode 
                      ? 'Projects section is hidden' 
                      : 'We have not yet extracted the individual projects for this portfolio.'}
                  </p>
                )}
              </div>
            </section>

            <section
              style={{
                backgroundColor: 'white',
                borderRadius: '20px',
                padding: '24px',
                boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)',
                border: '1px solid #e5e7eb',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <h2 style={{ margin: 0, color: '#0f172a' }}>Available analyses</h2>
                <button
                  onClick={loadPortfolios}
                  disabled={loading}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '6px',
                    border: '1px solid #d1d5db',
                    backgroundColor: 'white',
                    color: '#374151',
                    fontSize: '13px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    opacity: loading ? 0.6 : 1,
                  }}
                  title="Refresh portfolio list"
                >
                  {loading ? '⟳' : '↻'} Refresh
                </button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {portfolios.map((portfolio) => {
                  const isActive = portfolio.analysis_uuid === selectedPortfolioId;
                  const isDeleting = deletingIds[portfolio.analysis_uuid];
                  const projectNames = Array.isArray(portfolio.project_names)
                    ? portfolio.project_names.filter(Boolean)
                    : [];
                  const displayName = projectNames.length > 0 ? projectNames.join(', ') : 'Unnamed project';
                  
                  return (
                    <div
                      key={portfolio.analysis_uuid}
                      style={{
                        position: 'relative',
                        border: isActive ? '2px solid #2563eb' : '1px solid #e5e7eb',
                        borderRadius: '12px',
                        backgroundColor: isActive ? '#e0e7ff' : '#f8fafc',
                        overflow: 'hidden'
                      }}
                    >
                      <button
                        data-testid={`portfolio-card-${portfolio.analysis_uuid}`}
                        type="button"
                        onClick={() => handleSelectPortfolio(portfolio.analysis_uuid)}
                        disabled={isDeleting}
                        style={{
                          width: '100%',
                          textAlign: 'left',
                          padding: '16px',
                          border: 'none',
                          backgroundColor: 'transparent',
                          cursor: isDeleting ? 'not-allowed' : 'pointer',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '4px',
                          opacity: isDeleting ? 0.6 : 1,
                        }}
                      >
                        <span style={{ fontSize: '14px', fontWeight: '600', color: '#111827' }}>
                          {displayName}
                        </span>
                        <span style={{ fontSize: '13px', color: '#4b5563' }}>
                          {formatTimestamp(portfolio.analysis_timestamp)}
                        </span>
                        <span style={{ fontSize: '14px', color: '#2563eb' }}>
                          {portfolio.total_projects ?? 0} projects
                        </span>
                      </button>
                      
                      {/* Delete button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeletePortfolio(portfolio.analysis_uuid, displayName);
                        }}
                        disabled={isDeleting}
                        style={{
                          position: 'absolute',
                          top: '8px',
                          right: '8px',
                          width: '24px',
                          height: '24px',
                          border: 'none',
                          borderRadius: '50%',
                          backgroundColor: 'rgba(239, 68, 68, 0.1)',
                          color: '#dc2626',
                          cursor: isDeleting ? 'not-allowed' : 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '14px',
                          fontWeight: 'bold',
                          opacity: isDeleting ? 0.5 : 0.7,
                          transition: 'opacity 0.2s ease',
                        }}
                        onMouseEnter={(e) => { if (!isDeleting) e.target.style.opacity = '1'; }}
                        onMouseLeave={(e) => { if (!isDeleting) e.target.style.opacity = '0.7'; }}
                        title={`Delete ${displayName} analysis`}
                      >
                        {isDeleting ? '⋯' : '×'}
                      </button>
                    </div>
                  );
                })}
              </div>
            </section>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Portfolio;
