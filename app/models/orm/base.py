from sqlalchemy.orm import declarative_base


class CustomBase:
    def __repr__(self) -> str:
        # Get the class name (e.g., 'ExperimentORM')
        class_name = self.__class__.__name__

        # Get a list of (column_name, value) for all columns defined in the model
        columns = [
            # Check for attributes that are actually columns (skip relationships)
            (c.name, getattr(self, c.name))
            for c in self.__table__.columns
        ]

        # Format the output string: ClassName(column1=value1, column2=value2, ...)
        column_str = ", ".join(f"{name}={repr(value)}" for name, value in columns)

        return f"{class_name}({column_str})"

    def to_dict(self, include_relationships=False):
        """Converts the ORM object to a dictionary."""
        data = {}

        # Iterate over all mapped columns
        for column in self.__table__.columns:
            data[column.name] = getattr(self, column.name)

        if include_relationships:
            # Iterate over all defined relationships
            for name, relation in self.__mapper__.relationships.items():
                # Get the related object(s)
                related_object = getattr(self, name)

                if related_object is None:
                    data[name] = None
                elif relation.uselist:  # It's a list (e.g., variants = [...])
                    data[name] = [
                        item.to_dict(include_relationships=False)
                        for item in related_object
                    ]
                else:  # It's a single object
                    data[name] = related_object.to_dict(include_relationships=False)

        return data


Base = declarative_base(cls=CustomBase)

