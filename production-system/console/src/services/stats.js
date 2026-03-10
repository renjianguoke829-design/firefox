import pg from 'pg';

const { Pool } = pg;

export class StatsService {
  constructor(connectionString = process.env.DATABASE_URL) {
    this.pool = new Pool({ connectionString });
  }

  async query(text, params = []) {
    const client = await this.pool.connect();
    try {
      return await client.query(text, params);
    } finally {
      client.release();
    }
  }

  async getTodayStats() {
    const cards = await this.query(
      `SELECT COUNT(*)::int AS contradiction_count
       FROM contradiction_cards
       WHERE DATE(created_at) = CURRENT_DATE`
    );

    const runs = await this.query(
      `SELECT COUNT(*)::int AS pipeline_runs,
              COALESCE(AVG(duration_ms), 0)::int AS avg_duration_ms
       FROM pipeline_logs
       WHERE DATE(created_at) = CURRENT_DATE`
    );

    return {
      contradictionCount: cards.rows[0]?.contradiction_count ?? 0,
      pipelineRuns: runs.rows[0]?.pipeline_runs ?? 0,
      avgDurationMs: runs.rows[0]?.avg_duration_ms ?? 0
    };
  }

  async getWeekTrend() {
    const result = await this.query(
      `SELECT to_char(day, 'MM-DD') AS day,
              COUNT(c.id)::int AS output_count
       FROM generate_series(CURRENT_DATE - INTERVAL '6 day', CURRENT_DATE, INTERVAL '1 day') AS day
       LEFT JOIN contradiction_cards c
         ON DATE(c.created_at) = DATE(day)
       GROUP BY day
       ORDER BY day`
    );

    return result.rows.map((row) => ({
      day: row.day,
      outputCount: row.output_count
    }));
  }

  async getBottleneck() {
    const result = await this.query(
      `SELECT stage,
              COALESCE(AVG(duration_ms), 0)::int AS avg_duration_ms
       FROM pipeline_logs
       GROUP BY stage
       ORDER BY avg_duration_ms DESC`
    );

    const stages = result.rows.map((row) => ({
      stage: row.stage,
      avgDurationMs: row.avg_duration_ms
    }));

    return {
      stages,
      bottleneck: stages[0] || null
    };
  }

  async getQualityTrend() {
    const result = await this.query(
      `SELECT id::text,
              quality_score::int,
              created_at
       FROM contradiction_cards
       ORDER BY created_at DESC
       LIMIT 20`
    );

    return result.rows
      .reverse()
      .map((row, index) => ({
        index: index + 1,
        qualityScore: row.quality_score ?? 0,
        createdAt: row.created_at
      }));
  }

  async getRecentCards(limit = 5) {
    const result = await this.query(
      `SELECT title,
              LEFT(COALESCE(contradiction, facts, ''), 120) AS summary,
              created_at
       FROM contradiction_cards
       ORDER BY created_at DESC
       LIMIT $1`,
      [limit]
    );

    return result.rows.map((row) => ({
      title: row.title,
      summary: row.summary,
      createdAt: row.created_at
    }));
  }
}
