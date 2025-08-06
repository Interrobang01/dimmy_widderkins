import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

export class Markets {
  private db: sqlite3.Database;

  constructor() {
    this.initializeDatabase();
  }

  private async initializeDatabase() {
    // Open the SQLite database
    this.db = await open({
    filename: './markets.db',
    driver: sqlite3.Database,
    });
  }
}
