from sqlalchemy.orm import declarative_base


class CustomBase:
    def __repr__(self) -> str:
        class_name = self.__class__.__name__

        columns = [(c.name, getattr(self, c.name)) for c in self.__table__.columns]

        column_str = ", ".join(f"{name}={repr(value)}" for name, value in columns)

        return f"{class_name}({column_str})"

    def to_dict(self, include_relationships=False):
        """Converts the ORM object to a dictionary."""
        data = {}

        for column in self.__table__.columns:
            data[column.name] = getattr(self, column.name)

        if include_relationships:
            for name, relation in self.__mapper__.relationships.items():
                related_object = getattr(self, name)

                if related_object is None:
                    data[name] = None
                elif relation.uselist:  # It's a list (e.g., variants = [...])
                    data[name] = [
                        item.to_dict(include_relationships=False)
                        for item in related_object
                    ]
                else:
                    data[name] = related_object.to_dict(include_relationships=False)

        return data


Base = declarative_base(cls=CustomBase)
