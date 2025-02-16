import sqlite3
import json
import sys
import click
from flask import g, current_app
from flask.cli import with_appcontext
from pathlib import Path

class Db:
    def __init__(self):
        self.db = None

    def init_app(self, app):
        app.teardown_appcontext(self.close)
        app.cli.add_command(self.init_db_command)
        
        self.sql_root = Path(app.root_path) / 'sql'
        if not self.sql_root.exists():
            raise RuntimeError(f"SQL directory missing: {self.sql_root}")
        
        self._verify_sql_structure()
        
        app.config.setdefault('DATABASE', app.instance_path / 'flaskr.sqlite')

    def _verify_sql_structure(self):
        required_files = [
            'setup/create_table_words.sql',
            'setup/create_table_word_reviews.sql',
            'setup/create_table_groups.sql',
            'setup/create_table_word_review_items.sql',
            'setup/create_table_word_groups.sql',
            'setup/create_table_study_activities.sql',
            'setup/create_table_study_sessions.sql'
        ]
        
        for rel_path in required_files:
            target_path = self.sql_root / rel_path
            if not target_path.exists():
                raise RuntimeError(f"Missing SQL file: {target_path}")

    def get(self):
        if 'db' not in g:
            g.db = sqlite3.connect(current_app.config['DATABASE'])
            g.db.row_factory = sqlite3.Row
        return g.db

    def close(self, e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    def create_all(self):
        db = self.get()
        for sql_file in self.sql_root.glob('setup/*.sql'):
            db.executescript(sql_file.read_text())
        db.commit()

    @click.command('init-db')
    @with_appcontext
    def init_db_command(self):
        self.create_all()
        self.import_sample_data()
        click.echo('Initialized the database.')

    def import_sample_data(self):
        with self.get() as db:
            self.import_word_json(db, 'Core Verbs', 'seed/data_verbs.json')
            self.import_word_json(db, 'Core Adjectives', 'seed/data_adjectives.json')
            self.import_study_activities_json(db, 'seed/study_activities.json')

    def sql(self, filepath):
        target_file = self.sql_root / filepath
        if not target_file.exists():
            raise FileNotFoundError(f"SQL file {filepath} not found")
        return target_file.read_text(encoding='utf-8')

    def load_json(self, filepath):
        with open(filepath, 'r') as file:
            return json.load(file)

    def import_study_activities_json(self, db, data_json_path):
        study_activities = self.load_json(data_json_path)
        db.executemany('''
        INSERT INTO study_activities (name, url, preview_url) VALUES (?, ?, ?)
        ''', [(a['name'], a['url'], a['preview_url']) for a in study_activities])

    def import_word_json(self, db, group_name, data_json_path):
        db.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))
        group_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        words = self.load_json(data_json_path)
        db.executemany('''
        INSERT INTO words (kanji, romaji, english, parts) VALUES (?, ?, ?, ?)
        ''', [(w['kanji'], w['romaji'], w['english'], json.dumps(w['parts'])) for w in words])
        
        word_ids = db.execute('SELECT id FROM words ORDER BY id DESC LIMIT ?', (len(words),)).fetchall()
        db.executemany('INSERT INTO word_groups (word_id, group_id) VALUES (?, ?)',
                       [(w[0], group_id) for w in word_ids])
        
        db.execute('UPDATE groups SET words_count = ? WHERE id = ?', (len(words), group_id))
        click.echo(f"Added {len(words)} words to '{group_name}' group.")

    def environment_report(self):
        return {
            "python_version": sys.version,
            "os_platform": sys.platform,
            "working_directory": str(Path.cwd()),
            "script_location": str(Path(__file__).resolve().parent),
            "sql_root_verified": self.sql_root.exists()
        }

db = Db()
