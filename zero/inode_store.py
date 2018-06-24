import sqlite3


class InodeStore:
    """Converts between inode numbers and fuse paths"""

    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path, timeout=5)
        with self.connection:
            self.connection.execute(
                """CREATE TABLE IF NOT EXISTS inodes (nodepath text primary key, inode text)"""
            )
            # Initialize sequence, needs refactoring
            self.connection.execute(
                """CREATE TABLE IF NOT EXISTS sequences (name text primary key, value integer)"""
            )

    def create_and_get_inode(self, path):
        with self.connection:
            print("creating path", path)
            self._create_path(path)
            return self._get_inode(path)

    def get_inode(self, path):
        with self.connection:
            return self._get_inode(path)

    def get_paths(self, inode):
        with self.connection:
            cursor = self.connection.execute(
                """SELECT nodepath FROM inodes WHERE inode = ?""", (inode,)
            )
            return [result[0] for result in cursor.fetchall()]

    def delete_path(self, path):
        with self.connection:
            self._delete_path(path)

    def change_path(self, old_path, new_path):
        with self.connection:
            inode = self._get_inode(old_path)
            self._delete_path(old_path)
            self._create_path(new_path, inode)

    def _create_path(self, path, inode=None):
        if inode is None:
            inode = self._get_inode_sequence()
            self.connection.execute(
                # The problem is using max here is that I might re-use
                # old values if the old max is removed. Better would be
                # a sequence as it is supported by postgresql
                """INSERT INTO inodes (nodepath, inode) VALUES (?, ?)
                """,
                (path, inode),
            )
        else:
            self.connection.execute(
                """INSERT INTO inodes (nodepath, inode)
                VALUES (?, ?)
                """,
                (path, inode),
            )

    def _delete_path(self, path):
        self.connection.execute(
            """DELETE from inodes WHERE nodepath = ?""", (path,)
        )

    def _get_inode(self, path):
        cursor = self.connection.execute(
            """SELECT inode FROM inodes WHERE nodepath = ?""", (path,)
        )
        result = cursor.fetchone()
        # TODO: Why is the "or 0" here? Looks like it's not needed?
        return result and result[0] or 0

    def _get_inode_sequence(self):
        cursor = self.connection.execute(
            """SELECT value FROM sequences WHERE name='inode_sequence'"""
        )
        result = cursor.fetchone()
        value = result and result[0]
        if value is None:
            self.connection.execute(
                """INSERT INTO sequences (name, value) VALUES ('inode_sequence', 1)"""
            )
            value = 1
        self.connection.execute(
            """UPDATE sequences SET value=value+1 WHERE name='inode_sequence'"""
        )
        return value
