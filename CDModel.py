from message_processing.recording_processing import processing


class CAVGraph: 
    def __init__(self, component_categories):
        self.component_categories = component_categories
        self.components = {}
        for category in self.component_categories: 
            self.components[category] = []
        self.relations = {}

    def update_graph(self, new_info): 
        component_flag, relation_flag = 0, 0
        new_components = set()  # DEPRECATED
        updated_components = set()
        for category in self.component_categories: 
            new_component = self.update_component(category, new_info[category])
            if new_component: 
                component_flag += 1
                new_components.add(new_component)  # DEPRECATED
            updated_components.add(new_info[category])
        for i in range(1, len(self.component_categories)): 
            cause_node = new_info[self.component_categories[i-1]]
            result_node = new_info[self.component_categories[i]]
            if self.add_relation(cause_node, result_node): 
                relation_flag += 1
        if component_flag > 0: 
            # return True, new_components  # DEPRECATED
            return True, updated_components  # DEPRECATED
        else: 
            # return False, new_components  # DEPRECATED
            return False, updated_components  # DEPRECATED
    
    def update_component(self, component_category, new_info_item): 
        if not new_info_item in self.components[component_category]: 
            self.components[component_category].append(new_info_item)
            self.relations[new_info_item] = set()
            return new_info_item
        return None

    def add_relation(self, cause, result): 
        # Return True if add a new relation successfully, or else return False
        if result in self.relations[cause]: 
            return False
        else: 
            self.relations[cause].add(result)
            return True
    
    def show_relations(self):
        print('Detected relations in the CAV Graph: ')
        for category in self.component_categories: 
            for item in self.components[category]: 
                for nodes in self.relations[item]: 
                    print(f'    {item} ----> {nodes}')
    
    def add_graph(self, graph_temp): 
        for category in self.component_categories: 
            components_sum = set(self.components[category]) | set(graph_temp.components[category])
            self.components[category] = list(components_sum)
            for cause in self.components[category]: 
                if cause in self.relations and cause in graph_temp.relations: 
                    relations_sum_curr = self.relations[cause] | graph_temp.relations[cause]
                if cause not in self.relations and cause in graph_temp.relations: 
                    relations_sum_curr = graph_temp.relations[cause]
                if cause in self.relations and cause not in graph_temp.relations: 
                    relations_sum_curr = self.relations[cause]
                self.relations[cause] = relations_sum_curr